"""Utilities for translating existing VisualSpec structures into ScenePlans."""
from __future__ import annotations

from typing import Dict, List

from src.primitives.models import Act, Script, VisualSpec

from .scene_plan import (
    Anchor,
    BeatAction,
    PlanObject,
    ScenePlan,
    TimelineBeat,
    summarize_plan,
)

_DEFAULT_TOTAL_DURATION = 4.0
_MIN_DURATION = 0.5

_POSITION_TO_ANCHOR: Dict[str, Anchor] = {
    "center": Anchor.CENTER,
    "top": Anchor.TOP,
    "bottom": Anchor.BOTTOM,
    "left": Anchor.LEFT,
    "right": Anchor.RIGHT,
    "top_left": Anchor.TOP_LEFT,
    "top_right": Anchor.TOP_RIGHT,
    "bottom_left": Anchor.BOTTOM_LEFT,
    "bottom_right": Anchor.BOTTOM_RIGHT,
}


def _pick_anchor(position: str | None) -> Anchor:
    if position is None:
        return Anchor.CENTER
    return _POSITION_TO_ANCHOR.get(position.lower(), Anchor.CENTER)


def _coerce_metadata(params: Dict[str, object]) -> Dict[str, str]:
    coerced: Dict[str, str] = {}
    for key, value in params.items():
        coerced[key] = str(value)
    return coerced


def scene_plan_from_visual_spec(visual: VisualSpec, *, scene_id: str) -> ScenePlan:
    """Convert a single VisualSpec into a minimal ScenePlan."""

    object_id = f"{scene_id}_object"
    total_duration = max(visual.duration or _DEFAULT_TOTAL_DURATION, _MIN_DURATION)
    enter_duration = min(total_duration * 0.4, 1.2)
    hold_duration = max(total_duration - enter_duration, 0.1)

    plan_object = PlanObject(
        object_id=object_id,
        type=visual.type,
        anchor=_pick_anchor(visual.position),
        metadata={
            "content": visual.content,
            "animation_style": visual.animation_style or "",
            **_coerce_metadata(visual.params),
        },
    )

    timeline = [
        TimelineBeat(
            beat_id=f"{scene_id}_enter",
            subject=object_id,
            action=BeatAction.ENTER,
            start=0.0,
            duration=enter_duration,
            params={"style": visual.animation_style or "draw"},
        ),
        TimelineBeat(
            beat_id=f"{scene_id}_hold",
            subject=object_id,
            action=BeatAction.EMPHASIZE,
            start=enter_duration,
            duration=hold_duration,
            params={"style": visual.animation_style or "draw"},
        ),
    ]

    metadata = {"source_visual_type": visual.type}

    return ScenePlan(
        scene_id=scene_id,
        description=visual.content[:120],
        objects=[plan_object],
        timeline=timeline,
        metadata=metadata,
    )


def scene_plans_from_act(act: Act) -> List[ScenePlan]:
    """Convert an Act into one ScenePlan per visual."""

    plans: List[ScenePlan] = []
    for index, visual in enumerate(act.visuals):
        scene_id = f"{act.id}_scene_{index:02d}"
        plans.append(scene_plan_from_visual_spec(visual, scene_id=scene_id))
    return plans


def scene_plans_from_script(script: Script) -> List[ScenePlan]:
    """Convert a Script into scene plans for each contained VisualSpec."""

    plans: List[ScenePlan] = []
    for act in script.acts:
        plans.extend(scene_plans_from_act(act))
    return plans


def summarize_script_conversion(script: Script) -> List[str]:
    """Return human-readable summaries of all plans in the script."""

    return [summarize_plan(plan) for plan in scene_plans_from_script(script)]


__all__ = [
    "scene_plan_from_visual_spec",
    "scene_plans_from_act",
    "scene_plans_from_script",
    "summarize_script_conversion",
]
