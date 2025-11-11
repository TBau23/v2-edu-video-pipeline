"""
Visual rendering system - converts VisualSpecs to Manim scenes.

This is the most technically complex part of the pipeline. It takes declarative
VisualSpecs and generates actual Manim animation code, then renders it.

Key challenges:
1. Precise timing control (must match audio)
2. Meaningful animations (not just placeholders)
3. Style consistency (use StyleConfig)
4. Composability (multiple visuals in one scene)
"""

from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from manim import Scene, Text, MathTex, Axes, Write, FadeIn, FadeOut, Create, ReplacementTransform
from manim import config as manim_config, UP, DOWN, LEFT, RIGHT
import logging

from src.primitives.models import Act, VisualSpec, AudioSegment
from src.style.config import StyleConfig
from src.visuals.executor import SceneExecutor
from src.visuals.timing import VisualTimingCalculator, SyncPoint
# Note: generate_animation_scene is imported inside _render_animation to avoid circular imports

logger = logging.getLogger(__name__)


@dataclass
class RenderResult:
    """Result of rendering a visual."""
    output_path: Path
    duration: float
    visual_spec: VisualSpec


class VisualRenderer:
    """Renders VisualSpecs to video files using Manim.

    Architecture:
    - One renderer per Act (each Act is rendered as a separate scene)
    - Multiple VisualSpecs in an Act are composed into a single scene
    - Timing is controlled to match audio duration
    """

    def __init__(
        self,
        style: StyleConfig,
        output_dir: Path,
        quality: str = "medium_quality",
        openai_key: Optional[str] = None
    ):
        """Initialize renderer.

        Args:
            style: StyleConfig to use for consistent styling
            output_dir: Directory to save rendered videos
            quality: Render quality ('low_quality', 'medium_quality', 'high_quality')
            openai_key: OpenAI API key for LLM animation generation
        """
        self.style = style
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quality = quality
        self.openai_key = openai_key

        # Create executor for rendering
        self.executor = SceneExecutor(output_dir, quality=quality)

        # Configure Manim
        self._configure_manim()

    def _configure_manim(self):
        """Configure Manim with our style settings."""
        # Resolution
        width, height = self.style.layout.resolution
        manim_config.pixel_width = width
        manim_config.pixel_height = height
        manim_config.frame_rate = self.style.layout.fps

        # Background color
        manim_config.background_color = self.style.colors.background

        # Output settings
        manim_config.output_file = str(self.output_dir)
        manim_config.media_dir = str(self.output_dir.parent / "manim_media")

        # Performance settings for resource-constrained environments
        # Disable caching entirely since we never re-render the same content
        # This saves RAM and disk space with zero downside for one-time renders
        manim_config.disable_caching = True

        logger.info("Manim configured: caching disabled for optimal resource usage")

    def render_act(
        self,
        act: Act,
        audio: Optional[AudioSegment] = None,
        target_duration: Optional[float] = None
    ) -> RenderResult:
        """Render all visuals for an Act into a single video.

        Args:
            act: The Act to render
            audio: Audio segment with word timestamps (for precise sync)
            target_duration: Target duration in seconds (from audio)
                           If None, uses act.estimated_duration

        Returns:
            RenderResult with output path and actual duration
        """
        # Determine duration
        if audio:
            duration = audio.duration
        elif target_duration:
            duration = target_duration
        else:
            duration = act.estimated_duration or 10.0

        # Generate scene class dynamically
        scene_class = self._create_scene_for_act(act, audio, duration)

        # Render with Manim using the executor
        output_path = self.executor.render_scene(
            scene_class,
            output_name=act.id,
            preview=False
        )

        return RenderResult(
            output_path=output_path,
            duration=duration,
            visual_spec=act.visuals[0] if act.visuals else None
        )

    def _calculate_visual_timings(self, visuals: List[VisualSpec], target_duration: float) -> List[float]:
        """Calculate duration for each visual based on Act duration.

        Handles:
        - All explicit durations: use them (scale if sum > target)
        - Some explicit: fill remaining time with unspecified visuals
        - No explicit: divide equally

        Args:
            visuals: List of VisualSpecs
            target_duration: Total duration for the Act

        Returns:
            List of durations (one per visual)
        """
        if not visuals:
            return []

        # Count explicit vs implicit durations
        explicit_durations = [v.duration for v in visuals if v.duration is not None]
        num_unspecified = len(visuals) - len(explicit_durations)

        if num_unspecified == 0:
            # All durations specified
            total_explicit = sum(explicit_durations)

            if total_explicit > target_duration:
                # Scale down proportionally
                scale = target_duration / total_explicit
                return [v.duration * scale for v in visuals]
            else:
                # Use as-is (might be shorter than target, that's okay)
                return [v.duration for v in visuals]

        else:
            # Some durations missing
            total_explicit = sum(explicit_durations)
            remaining_time = max(0, target_duration - total_explicit)
            time_per_unspecified = remaining_time / num_unspecified if num_unspecified > 0 else 0

            durations = []
            for v in visuals:
                if v.duration is not None:
                    durations.append(v.duration)
                else:
                    durations.append(time_per_unspecified)

            return durations

    def _create_scene_for_act(
        self,
        act: Act,
        audio: Optional[AudioSegment],
        duration: float
    ) -> type:
        """Create a Manim Scene class for an Act.

        This dynamically generates a Scene class with the construct() method
        that renders all the visuals in the act with proper timing.

        Args:
            act: The Act to create a scene for
            audio: Audio segment with word timestamps (for sync)
            duration: Total duration for the scene

        Returns:
            A Scene subclass ready to be rendered
        """
        style = self.style
        visuals = act.visuals
        openai_key = self.openai_key  # Capture for use in nested Scene class
        output_dir = self.output_dir  # Capture for use in nested Scene class
        quality = self.quality  # Capture for use in nested Scene class

        # Calculate timing using sync points (audio-aware if available)
        timing_calc = VisualTimingCalculator()
        sync_points = timing_calc.calculate_sync_points(visuals, audio, duration)

        class ActScene(Scene):
            def construct(self):
                # Track current time for wait() calculations
                scene_time = 0.0

                for sync_point in sync_points:
                    # Wait until visual should appear
                    wait_time = sync_point.start_time - scene_time
                    if wait_time > 0:
                        self.wait(wait_time)
                        scene_time += wait_time

                    # Render the visual
                    visual = sync_point.visual_spec
                    visual_duration = sync_point.duration

                    # Render based on type
                    if visual.type == "equation":
                        self._render_equation(visual, visual_duration)
                    elif visual.type == "text":
                        self._render_text(visual, visual_duration)
                    elif visual.type == "graph":
                        self._render_graph(visual, visual_duration)
                    elif visual.type == "animation":
                        self._render_animation(visual, visual_duration)
                    elif visual.type == "diagram":
                        self._render_diagram(visual, visual_duration)

                    scene_time += visual_duration

            def _render_equation(self, visual: VisualSpec, duration: float):
                """Render an equation."""
                color = style.colors.equation_color
                font_size = visual.params.get("font_size", style.typography.equation_size)

                # Create equation
                equation = MathTex(
                    visual.content,
                    color=color,
                    font_size=font_size
                )

                # Position
                equation = self._apply_position(equation, visual.position)

                # Animate
                if visual.animation_style == "write":
                    self.play(Write(equation), run_time=duration)
                elif visual.animation_style == "fade":
                    self.play(FadeIn(equation), run_time=duration)
                else:
                    self.add(equation)
                    self.wait(duration)

            def _render_text(self, visual: VisualSpec, duration: float):
                """Render text."""
                color = visual.params.get("color", style.colors.primary)
                if color == "accent":
                    color = style.colors.accent
                elif color == "primary":
                    color = style.colors.primary

                font_size = visual.params.get("font_size", style.typography.body_size)

                text = Text(
                    visual.content,
                    color=color,
                    font_size=font_size
                )

                text = self._apply_position(text, visual.position)

                if visual.animation_style == "write":
                    self.play(Write(text), run_time=duration)
                elif visual.animation_style == "fade":
                    self.play(FadeIn(text), run_time=duration)
                else:
                    self.add(text)
                    self.wait(duration)

            def _render_graph(self, visual: VisualSpec, duration: float):
                """Render a graph."""
                params = visual.params

                # Extract graph parameters
                x_range = params.get("x_range", [0, 10, 1])
                y_range = params.get("y_range", [0, 10, 1])
                x_label = params.get("x_label", "x")
                y_label = params.get("y_label", "y")

                # Create axes
                axes = Axes(
                    x_range=x_range,
                    y_range=y_range,
                    x_length=6,
                    y_length=4,
                    axis_config={"color": style.colors.secondary},
                )

                # Add labels
                x_label_mob = axes.get_x_axis_label(x_label)
                y_label_mob = axes.get_y_axis_label(y_label)

                # Position
                graph_group = axes  # TODO: Group with labels
                graph_group = self._apply_position(graph_group, visual.position)

                # Animate
                self.play(Create(axes), run_time=duration * 0.5)

                # TODO: Plot function if specified
                # function = params.get("function")
                # if function:
                #     plot = axes.plot(lambda x: eval(function))
                #     self.play(Create(plot), run_time=duration * 0.5)

            def _render_animation(self, visual: VisualSpec, duration: float):
                """Render animation using LLM generation.

                Generates inline Manim code and executes it directly in this scene.
                """
                description = visual.content
                logger.info(f"Generating LLM animation: {description[:50]}...")

                try:
                    # Generate inline animation code
                    from src.visuals.llm_animator import generate_animation_scene
                    code = generate_animation_scene(
                        description=description,
                        duration=duration,
                        api_key=openai_key
                    )

                    # Execute code directly in this scene's context
                    # The code should use `self.play()`, `self.wait()`, etc.
                    logger.debug(f"Executing inline animation code:\n{code}")

                    # Import Manim objects that the generated code might use
                    from manim import Circle, Square, Rectangle, Dot, Arrow, Line, Text, MathTex, VGroup
                    from manim import FadeIn, FadeOut, Create, Write, Transform, ReplacementTransform
                    from manim import Indicate, FocusOn
                    from manim import UP, DOWN, LEFT, RIGHT, ORIGIN
                    from manim import BLUE, RED, GREEN, YELLOW, ORANGE, PURPLE, PINK
                    from manim import GRAY, DARK_GRAY, LIGHT_GRAY, WHITE, BLACK

                    # Execute the generated code in this scene's context
                    exec(code, {'self': self, '__builtins__': __builtins__,
                                'Circle': Circle, 'Square': Square, 'Rectangle': Rectangle,
                                'Dot': Dot, 'Arrow': Arrow, 'Line': Line,
                                'Text': Text, 'MathTex': MathTex, 'VGroup': VGroup,
                                'FadeIn': FadeIn, 'FadeOut': FadeOut, 'Create': Create,
                                'Write': Write, 'Transform': Transform, 'ReplacementTransform': ReplacementTransform,
                                'Indicate': Indicate, 'FocusOn': FocusOn,
                                'UP': UP, 'DOWN': DOWN, 'LEFT': LEFT, 'RIGHT': RIGHT, 'ORIGIN': ORIGIN,
                                'BLUE': BLUE, 'RED': RED, 'GREEN': GREEN, 'YELLOW': YELLOW,
                                'ORANGE': ORANGE, 'PURPLE': PURPLE, 'PINK': PINK,
                                'GRAY': GRAY, 'DARK_GRAY': DARK_GRAY, 'LIGHT_GRAY': LIGHT_GRAY,
                                'WHITE': WHITE, 'BLACK': BLACK})

                    logger.info(f"✓ LLM animation executed successfully")

                except Exception as e:
                    # Animation generation failed, show error placeholder
                    logger.error(f"LLM animation failed: {e}")
                    import traceback
                    logger.debug(f"Traceback:\n{traceback.format_exc()}")

                    placeholder = Text(
                        f"[Animation error]",
                        font_size=24,
                        color=style.colors.secondary
                    )
                    placeholder = self._apply_position(placeholder, visual.position)
                    self.play(FadeIn(placeholder), run_time=duration * 0.2)
                    self.wait(duration * 0.6)
                    self.play(FadeOut(placeholder), run_time=duration * 0.2)

            def _render_diagram(self, visual: VisualSpec, duration: float):
                """Render a diagram."""
                # TODO: Build diagram rendering system
                # For now, placeholder
                placeholder = Text(
                    f"[Diagram: {visual.content[:50]}...]",
                    font_size=24,
                    color=style.colors.secondary
                )

                placeholder = self._apply_position(placeholder, visual.position)
                self.play(FadeIn(placeholder), run_time=duration)

            def _apply_position(self, mobject, position: str):
                """Apply position to a mobject."""
                if position == "top":
                    mobject.to_edge(UP)
                elif position == "bottom":
                    mobject.to_edge(DOWN)
                elif position == "left":
                    mobject.to_edge(LEFT)
                elif position == "right":
                    mobject.to_edge(RIGHT)
                # "center" is default

                return mobject

        return ActScene


def render_act_to_file(
    act: Act,
    style: StyleConfig,
    output_path: Path,
    target_duration: Optional[float] = None
) -> RenderResult:
    """Convenience function to render a single act.

    Args:
        act: Act to render
        style: StyleConfig for styling
        output_path: Where to save the rendered video
        target_duration: Target duration (from audio timing)

    Returns:
        RenderResult with output path and duration
    """
    renderer = VisualRenderer(style, output_path.parent)
    return renderer.render_act(act, target_duration)
