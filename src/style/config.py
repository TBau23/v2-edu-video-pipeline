"""
Style configuration system for consistent video aesthetics.

All visual styling tokens are defined here to ensure consistency across videos.
Style configs are stored as JSON and can be versioned/shared.
"""

from typing import Optional, Dict, Tuple
from pydantic import BaseModel, Field


class ColorPalette(BaseModel):
    """Color scheme for the video."""

    background: str = Field(default="#0f0f0f", description="Background color (hex)")
    primary: str = Field(default="#ffffff", description="Primary text/content color (hex)")
    accent: str = Field(default="#58a6ff", description="Accent/highlight color (hex)")
    secondary: str = Field(default="#8b949e", description="Secondary text color (hex)")

    # Semantic colors
    equation_color: str = Field(default="#58a6ff", description="Default equation color (hex)")
    highlight_color: str = Field(default="#f78166", description="Color for highlights/emphasis (hex)")
    graph_colors: list[str] = Field(
        default_factory=lambda: ["#58a6ff", "#f78166", "#56d364", "#e3b341"],
        description="Colors for graphs/data (hex)"
    )


class Typography(BaseModel):
    """Font and text styling."""

    font_family: str = Field(default="Helvetica", description="Primary font family")
    base_font_size: int = Field(default=36, description="Base font size in points")

    # Specific text sizes
    title_size: int = Field(default=72, description="Title text size")
    heading_size: int = Field(default=48, description="Heading text size")
    body_size: int = Field(default=36, description="Body text size")
    equation_size: int = Field(default=48, description="Equation text size")
    caption_size: int = Field(default=28, description="Caption/small text size")


class AnimationTiming(BaseModel):
    """Timing parameters for animations."""

    # Transition durations
    fade_duration: float = Field(default=0.3, description="Fade in/out duration (seconds)")
    write_duration: float = Field(default=1.0, description="Text/equation write duration (seconds)")
    draw_duration: float = Field(default=1.5, description="Drawing/morphing duration (seconds)")

    # Pauses
    pause_after_title: float = Field(default=0.5, description="Pause after title appears (seconds)")
    pause_between_acts: float = Field(default=0.3, description="Pause between acts (seconds)")
    pause_after_equation: float = Field(default=0.8, description="Pause after equation appears (seconds)")

    # Easing
    default_easing: str = Field(default="smooth", description="Default animation easing function")


class VoiceConfig(BaseModel):
    """Voice/TTS configuration."""

    provider: str = Field(default="openai", description="TTS provider: 'openai' or 'elevenlabs'")
    voice_id: str = Field(default="alloy", description="Voice ID/name from provider")

    # Speech parameters
    speed: float = Field(default=1.0, description="Speech speed multiplier (0.5-2.0)")
    pitch: Optional[float] = Field(default=None, description="Pitch adjustment (if supported)")

    # Natural pauses (added to narration text)
    add_pauses: bool = Field(
        default=True,
        description="Automatically add pauses for punctuation"
    )
    pause_markers: Dict[str, float] = Field(
        default_factory=lambda: {
            ".": 0.5,
            ",": 0.3,
            "?": 0.6,
            "!": 0.6,
        },
        description="Pause duration (seconds) for punctuation marks"
    )


class LayoutConfig(BaseModel):
    """Layout and positioning configuration."""

    # Video dimensions
    resolution: Tuple[int, int] = Field(default=(1920, 1080), description="Video resolution (width, height)")
    fps: int = Field(default=30, description="Frames per second")

    # Margins and spacing
    margin: int = Field(default=100, description="Edge margin in pixels")
    content_padding: int = Field(default=50, description="Padding between content elements")

    # Positioning presets
    title_position: str = Field(default="top", description="Default title position")
    equation_position: str = Field(default="center", description="Default equation position")


class StyleConfig(BaseModel):
    """Complete style configuration for video generation.

    This model brings together all styling concerns in one place.
    Store as JSON for versioning and sharing across projects.
    """
    name: str = Field(default="default", description="Style config name/identifier")

    colors: ColorPalette = Field(default_factory=ColorPalette)
    typography: Typography = Field(default_factory=Typography)
    animation: AnimationTiming = Field(default_factory=AnimationTiming)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)

    # Metadata
    description: Optional[str] = Field(
        default=None,
        description="Description of this style (e.g., 'Dark mode with blue accents')"
    )

    @classmethod
    def load_preset(cls, preset_name: str = "default") -> "StyleConfig":
        """Load a preset style configuration.

        Args:
            preset_name: Name of the preset ("default", "dark", "light", etc.)

        Returns:
            StyleConfig instance with preset values
        """
        # For now, just return default
        # In the future, we can load from preset files
        return cls(name=preset_name, description=f"{preset_name.title()} preset style")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "default",
                "description": "Default dark theme with blue accents",
                "colors": {
                    "background": "#0f0f0f",
                    "primary": "#ffffff",
                    "accent": "#58a6ff"
                },
                "typography": {
                    "font_family": "Helvetica",
                    "base_font_size": 36
                },
                "voice": {
                    "provider": "openai",
                    "voice_id": "alloy"
                }
            }
        }
