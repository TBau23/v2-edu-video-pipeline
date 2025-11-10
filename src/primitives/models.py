"""
Core primitive models for the video generation pipeline.

These models define the fundamental building blocks that make up a video:
- VisualSpec: declarative description of what to show on screen
- Act: a single video segment (narration + visuals + timing)
- AudioSegment: generated audio with timing metadata
- Script: collection of Acts representing the full video
"""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class VisualSpec(BaseModel):
    """Declarative description of visual content for a video segment.

    This model describes WHAT to show, not HOW to render it.
    The rendering engine (Manim) will interpret these specs.
    """
    type: Literal["equation", "graph", "animation", "diagram", "text"]

    # Content to display
    content: str = Field(
        ...,
        description="The actual content: LaTeX for equations, description for animations, etc."
    )

    # Animation directives
    animation_style: Optional[str] = Field(
        default="draw",
        description="How this visual should appear: 'draw', 'fade', 'write', 'morph'"
    )

    duration: Optional[float] = Field(
        default=None,
        description="How long this visual should animate (seconds). None means auto-calculate."
    )

    # Timing and synchronization
    trigger_words: Optional[List[str]] = Field(
        default=None,
        description="Words in narration that trigger this visual (for audio sync)"
    )

    lead_time: Optional[float] = Field(
        default=0.5,
        description="Show visual this many seconds BEFORE trigger word (for anticipation)"
    )

    # Positioning and layout
    position: Optional[str] = Field(
        default="center",
        description="Where on screen: 'center', 'top', 'bottom', 'left', 'right'"
    )

    # Additional parameters for specific visual types
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific parameters (e.g., color for equations, axis ranges for graphs)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "equation",
                "content": "F = ma",
                "animation_style": "write",
                "position": "center",
                "params": {"color": "blue", "font_size": 48}
            }
        }


class Act(BaseModel):
    """A single segment of the video (one 'act' or 'scene').

    Represents a cohesive unit of content with narration and visuals.
    Acts are the primary unit of iteration - you can regenerate or edit individual acts.
    """
    id: str = Field(..., description="Unique identifier for this act (e.g., 'act_1_motivation')")

    # Content
    narration: str = Field(
        ...,
        description="The spoken narration text for this act"
    )

    visuals: List[VisualSpec] = Field(
        default_factory=list,
        description="Visual elements to show during this act"
    )

    # Timing hints (actual timing determined after audio generation)
    estimated_duration: Optional[float] = Field(
        default=None,
        description="Estimated duration in seconds (used for planning)"
    )

    # Metadata
    purpose: Optional[str] = Field(
        default=None,
        description="What this act accomplishes (e.g., 'motivate the problem', 'explain equation')"
    )

    notes: Optional[str] = Field(
        default=None,
        description="Internal notes for iteration and debugging"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "act_1_motivation",
                "narration": "Imagine you're in a car that suddenly brakes. You feel your body lurch forward. Why?",
                "visuals": [
                    {
                        "type": "animation",
                        "content": "car_braking_with_passenger",
                        "animation_style": "play",
                        "position": "center"
                    }
                ],
                "purpose": "Motivate Newton's First Law with relatable example"
            }
        }


class AudioSegment(BaseModel):
    """Generated audio for one Act with timing metadata."""

    act_id: str = Field(..., description="ID of the Act this audio corresponds to")

    # File reference
    audio_path: Path = Field(..., description="Path to the generated audio file (.mp3 or .wav)")

    # Timing data
    duration: float = Field(..., description="Total duration of the audio in seconds")

    # Word-level timestamps (if available from TTS provider)
    word_timestamps: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Word-level timing data for precise sync [{word: str, start: float, end: float}]"
    )

    # TTS metadata
    provider: str = Field(..., description="TTS provider used (e.g., 'openai', 'elevenlabs')")
    voice_id: Optional[str] = Field(default=None, description="Voice ID or name used")

    class Config:
        json_schema_extra = {
            "example": {
                "act_id": "act_1_motivation",
                "audio_path": "projects/newtons_first/audio/act_1.mp3",
                "duration": 8.5,
                "provider": "openai",
                "voice_id": "alloy"
            }
        }


class Script(BaseModel):
    """Complete video script - a collection of Acts with metadata.

    This is the main artifact from the script generation phase.
    Users can edit this JSON to iterate on the video structure.
    """
    # Metadata
    title: str = Field(..., description="Title of the video")
    topic: str = Field(..., description="Main topic being taught")

    # Content structure
    acts: List[Act] = Field(
        ...,
        description="Ordered list of Acts that make up the video"
    )

    # Generation metadata
    source_prompt: str = Field(..., description="Original user prompt that generated this script")

    style_profile: Optional[str] = Field(
        default="default",
        description="Name of the style config to use (references a style file)"
    )

    # Computed properties
    @property
    def estimated_total_duration(self) -> float:
        """Total estimated duration across all acts."""
        return sum(
            act.estimated_duration for act in self.acts
            if act.estimated_duration is not None
        )

    @property
    def act_count(self) -> int:
        """Number of acts in this script."""
        return len(self.acts)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Newton's First Law of Motion",
                "topic": "inertia and constant velocity",
                "source_prompt": "Teach Newton's First Law with real-world examples",
                "acts": [
                    {
                        "id": "act_1_motivation",
                        "narration": "Why do objects keep moving?",
                        "visuals": [],
                        "purpose": "Hook the viewer"
                    }
                ]
            }
        }


class VideoProject(BaseModel):
    """Complete video project - combines script, audio, and metadata.

    This is the top-level model that represents a full project workspace.
    """
    project_id: str = Field(..., description="Unique project identifier")

    script: Script = Field(..., description="The video script")

    audio_segments: List[AudioSegment] = Field(
        default_factory=list,
        description="Generated audio for each act"
    )

    # Project metadata
    workspace_path: Path = Field(..., description="Root directory for this project")

    # Status tracking
    status: Literal["script_only", "audio_generated", "visuals_generated", "assembled"] = Field(
        default="script_only",
        description="Current stage of the project pipeline"
    )

    # Output paths
    preview_video_path: Optional[Path] = Field(
        default=None,
        description="Path to low-res preview video"
    )

    final_video_path: Optional[Path] = Field(
        default=None,
        description="Path to final high-res video"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "newtons_first_law_2025_01_07",
                "workspace_path": "projects/newtons_first_law_2025_01_07",
                "status": "script_only"
            }
        }
