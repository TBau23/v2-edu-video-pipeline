"""Structured scene planning models for deterministic animation layout and timing.

This module introduces a typed schema describing the intermediate representation
between the high-level `VisualSpec` objects and the rendering layer.  The goal is
for planners (LLMs or heuristics) to author `ScenePlan` documents that explicitly
capture layout, relationships, and timeline beats so downstream stages can reason
about collisions and orchestration deterministically.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class Anchor(str, Enum):
    """Screen anchors used for coarse positioning."""

    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class Axis(str, Enum):
    """Axes that constraints can reference."""

    HORIZONTAL = "x"
    VERTICAL = "y"
    DEPTH = "z"


class ObjectRole(str, Enum):
    """High-level semantic role for planned objects."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    ANNOTATION = "annotation"
    AUXILIARY = "auxiliary"


class PlanObject(BaseModel):
    """Renderable object that will exist within the scene."""

    object_id: str = Field(..., description="Unique identifier for the object within the plan")
    type: str = Field(..., description="Object type (equation, axis, diagram, etc.)")
    role: ObjectRole = Field(
        default=ObjectRole.PRIMARY,
        description="Semantic role so layout/timeline heuristics can assign priorities.",
    )
    anchor: Anchor = Field(
        default=Anchor.CENTER,
        description="Preferred on-screen anchor if no constraints override it.",
    )
    z_index: int = Field(
        default=0,
        description="Stacking order used during rendering (larger numbers render on top).",
    )
    preferred_size: Optional[List[float]] = Field(
        default=None,
        description="Optional width/height hint (in frame-relative units).",
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional authoring metadata (e.g. color, label text, glyph ids).",
    )

    @validator("preferred_size")
    def _validate_preferred_size(cls, value: Optional[List[float]]) -> Optional[List[float]]:
        if value is None:
            return value
        if len(value) != 2:
            raise ValueError("preferred_size must be [width, height] if provided")
        if any(d <= 0 for d in value):
            raise ValueError("preferred_size dimensions must be positive")
        return value


class ConstraintType(str, Enum):
    ALIGN = "align"
    OFFSET = "offset"
    STACK = "stack"


class LayoutConstraint(BaseModel):
    """Relationship describing how one object relates to another in space."""

    subject: str = Field(..., description="ID of the object being constrained")
    target: Optional[str] = Field(
        default=None,
        description="ID of the reference object (None means frame reference).",
    )
    type: ConstraintType = Field(..., description="Constraint primitive")
    axis: Optional[Axis] = Field(
        default=None,
        description="Relevant axis when applicable (align/offset).",
    )
    gap: float = Field(
        default=0.0,
        description="Spacing applied for stack/offset relationships (frame-relative units).",
    )
    anchor: Optional[Anchor] = Field(
        default=None,
        description="Optional anchor override for align constraints.",
    )

    @root_validator
    def _validate_constraint(cls, values: Dict[str, object]) -> Dict[str, object]:
        constraint_type: ConstraintType = values["type"]
        axis: Optional[Axis] = values.get("axis")
        anchor: Optional[Anchor] = values.get("anchor")

        if constraint_type in {ConstraintType.ALIGN, ConstraintType.OFFSET} and axis is None:
            raise ValueError("align/offset constraints must specify an axis")
        if constraint_type == ConstraintType.ALIGN and anchor is None:
            raise ValueError("align constraints require an anchor to align to")
        if constraint_type == ConstraintType.STACK and axis not in {Axis.HORIZONTAL, Axis.VERTICAL}:
            raise ValueError("stack constraints must specify horizontal or vertical axis")
        return values


class BeatAction(str, Enum):
    ENTER = "enter"
    EXIT = "exit"
    EMPHASIZE = "emphasize"
    MOVE = "move"
    TRANSFORM = "transform"


class TimelineBeat(BaseModel):
    """Single beat within the scene timeline."""

    beat_id: str = Field(..., description="Unique identifier for the beat")
    subject: str = Field(..., description="Object impacted by this beat")
    action: BeatAction = Field(..., description="Action performed during the beat")
    start: float = Field(..., ge=0.0, description="Start time in seconds")
    duration: float = Field(..., gt=0.0, description="Duration in seconds")
    easing: str = Field(default="linear", description="Easing preset identifier")
    params: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional action-specific parameters (direction, emphasis level, etc.).",
    )


class ScenePlan(BaseModel):
    """Complete planned scene representation prior to rendering."""

    scene_id: str = Field(..., description="Identifier for the scene/shot")
    description: Optional[str] = Field(
        default=None,
        description="Human readable summary explaining the pedagogical intent.",
    )
    objects: List[PlanObject] = Field(..., description="Objects present in the scene")
    constraints: List[LayoutConstraint] = Field(
        default_factory=list,
        description="Spatial relationships between planned objects.",
    )
    timeline: List[TimelineBeat] = Field(
        default_factory=list,
        description="Ordered list of timeline beats describing motion/visibility.",
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Scene-level metadata (backgrounds, narration cues, etc.).",
    )

    @validator("objects")
    def _require_unique_object_ids(cls, objects: List[PlanObject]) -> List[PlanObject]:
        ids = [obj.object_id for obj in objects]
        if len(ids) != len(set(ids)):
            raise ValueError("scene plan contains duplicate object_ids")
        return objects

    @validator("timeline")
    def _validate_timeline_order(cls, beats: List[TimelineBeat]) -> List[TimelineBeat]:
        ids = [beat.beat_id for beat in beats]
        if len(ids) != len(set(ids)):
            raise ValueError("scene plan contains duplicate timeline beat ids")
        previous_end = 0.0
        for beat in beats:
            if beat.start < previous_end - 1e-6:
                raise ValueError(
                    "timeline beats must be in non-decreasing start order;"
                    f" beat {beat.beat_id} starts at {beat.start}, which is before {previous_end}"
                )
            previous_end = max(previous_end, beat.start + beat.duration)
        return beats

    @root_validator
    def _validate_references(cls, values: Dict[str, object]) -> Dict[str, object]:
        object_ids = {obj.object_id for obj in values.get("objects", [])}

        for constraint in values.get("constraints", []):
            if constraint.subject not in object_ids:
                raise ValueError(
                    f"layout constraint references unknown subject '{constraint.subject}'"
                )
            if constraint.target is not None and constraint.target not in object_ids:
                raise ValueError(
                    f"layout constraint references unknown target '{constraint.target}'"
                )

        for beat in values.get("timeline", []):
            if beat.subject not in object_ids:
                raise ValueError(f"timeline beat references unknown subject '{beat.subject}'")

        return values


def summarize_plan(plan: ScenePlan) -> str:
    """Produce a concise human-readable summary for debugging/logging."""

    object_summary = ", ".join(
        f"{obj.object_id}:{obj.type}@{obj.anchor.value}" for obj in plan.objects
    )
    beat_summary = ", ".join(
        f"{beat.beat_id}:{beat.action.value}@{beat.start:.2f}s/{beat.duration:.2f}s"
        for beat in plan.timeline
    )
    constraint_summary = ", ".join(
        f"{c.subject}->{c.target or 'frame'}:{c.type.value}" for c in plan.constraints
    ) or "none"
    return (
        f"ScenePlan(scene_id={plan.scene_id}, objects=[{object_summary}], "
        f"constraints=[{constraint_summary}], timeline=[{beat_summary}])"
    )
