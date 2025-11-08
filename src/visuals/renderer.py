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
from manim import config as manim_config

from src.primitives.models import Act, VisualSpec
from src.style.config import StyleConfig


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

    def __init__(self, style: StyleConfig, output_dir: Path):
        """Initialize renderer.

        Args:
            style: StyleConfig to use for consistent styling
            output_dir: Directory to save rendered videos
        """
        self.style = style
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

    def render_act(
        self,
        act: Act,
        target_duration: Optional[float] = None
    ) -> RenderResult:
        """Render all visuals for an Act into a single video.

        Args:
            act: The Act to render
            target_duration: Target duration in seconds (from audio)
                           If None, uses act.estimated_duration

        Returns:
            RenderResult with output path and actual duration
        """
        duration = target_duration or act.estimated_duration or 10.0

        # Generate scene class dynamically
        scene_class = self._create_scene_for_act(act, duration)

        # Render with Manim
        output_path = self.output_dir / f"{act.id}.mp4"

        # TODO: Actually render the scene
        # This requires calling Manim's rendering system programmatically
        # For now, return placeholder

        return RenderResult(
            output_path=output_path,
            duration=duration,
            visual_spec=act.visuals[0] if act.visuals else None
        )

    def _create_scene_for_act(self, act: Act, duration: float) -> type:
        """Create a Manim Scene class for an Act.

        This dynamically generates a Scene class with the construct() method
        that renders all the visuals in the act with proper timing.

        Args:
            act: The Act to create a scene for
            duration: Total duration for the scene

        Returns:
            A Scene subclass ready to be rendered
        """
        style = self.style
        visuals = act.visuals

        class ActScene(Scene):
            def construct(self):
                # Render each visual in sequence
                current_time = 0

                for visual in visuals:
                    # Determine visual duration
                    visual_duration = visual.duration or (duration / len(visuals))

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

                    current_time += visual_duration

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
                """Render a custom animation.

                This is the hardest part - creating meaningful physics animations
                from text descriptions.
                """
                # TODO: This requires building a library of reusable animations
                # For now, just show placeholder text
                placeholder = Text(
                    f"[Animation: {visual.content[:50]}...]",
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
                    mobject.to_edge("UP")
                elif position == "bottom":
                    mobject.to_edge("DOWN")
                elif position == "left":
                    mobject.to_edge("LEFT")
                elif position == "right":
                    mobject.to_edge("RIGHT")
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
