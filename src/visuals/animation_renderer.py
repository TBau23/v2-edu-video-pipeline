"""
Deterministic animation renderer - converts StructuredAnimationSpec to Manim code.

This is the core of the structured animation system. It takes declarative
StructuredAnimationSpec objects and generates Manim scenes deterministically
(without LLM calls), solving the two-LLM translation problem.

Key features:
- Rule-based interpretation of AnimationObjects, AnimationSteps, AnimationRelationships
- Pattern-specific optimizations for common educational animation patterns
- Precise timing control matching audio narration
- Fallback to placeholder rendering for unrecognized patterns
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

from manim import (
    Circle, Square, Rectangle, Dot, Arrow, Line, Text, MathTex, VGroup,
    FadeIn, FadeOut, Create, Write, Transform, ReplacementTransform,
    Indicate, FocusOn, GrowFromCenter, Shrink, Flash,
    UP, DOWN, LEFT, RIGHT, ORIGIN,
    BLUE, RED, GREEN, YELLOW, ORANGE, PURPLE, PINK,
    GRAY, DARK_GRAY, LIGHT_GRAY, WHITE, BLACK
)

from src.primitives.models import (
    StructuredAnimationSpec,
    AnimationObject,
    AnimationStep,
    AnimationRelationship
)

logger = logging.getLogger(__name__)


# Color mapping from string to Manim colors
COLOR_MAP = {
    "BLUE": BLUE, "RED": RED, "GREEN": GREEN, "YELLOW": YELLOW,
    "ORANGE": ORANGE, "PURPLE": PURPLE, "PINK": PINK,
    "GRAY": GRAY, "DARK_GRAY": DARK_GRAY, "LIGHT_GRAY": LIGHT_GRAY,
    "WHITE": WHITE, "BLACK": BLACK
}

# Shape mapping from string to Manim mobjects
SHAPE_MAP = {
    "circle": Circle,
    "rectangle": Rectangle,
    "square": Square,
    "dot": Dot,
    "arrow": Arrow,
    "line": Line
}


@dataclass
class RenderContext:
    """Context for rendering - tracks created objects and timing."""
    mobjects: Dict[str, Any]  # id -> Manim mobject
    current_time: float = 0.0
    scene_duration: float = 0.0


class AnimationRenderer:
    """Converts StructuredAnimationSpec to inline Manim code.

    This renderer generates executable Python code that can be run directly
    in a Manim Scene.construct() method.

    Architecture:
    - _render_object(): Creates Manim mobject from AnimationObject
    - _render_step(): Generates Manim animation from AnimationStep
    - _apply_pattern_optimization(): Optimizes for common educational patterns
    - render(): Main entry point that orchestrates rendering
    """

    def __init__(self):
        """Initialize the renderer."""
        pass

    def render(self, spec: StructuredAnimationSpec) -> str:
        """Convert StructuredAnimationSpec to executable Manim code.

        Returns Python code that can be exec'd in a Scene's construct() method.
        The code uses `self.play()`, `self.wait()`, etc.

        Args:
            spec: The structured animation specification

        Returns:
            Python code string ready to execute in Manim Scene
        """
        logger.info(f"Rendering structured animation: {spec.concept_being_taught}")
        logger.info(f"  Pattern hint: {spec.pattern_hint}")
        logger.info(f"  Objects: {len(spec.objects)}")
        logger.info(f"  Steps: {len(spec.progression)}")

        # Check for pattern-specific optimization
        if spec.pattern_hint:
            optimized_code = self._apply_pattern_optimization(spec)
            if optimized_code:
                logger.info(f"  ✓ Used pattern optimization: {spec.pattern_hint}")
                return optimized_code

        # Fall back to step-by-step rendering
        logger.info("  Using step-by-step rendering")
        return self._render_generic(spec)

    def _apply_pattern_optimization(self, spec: StructuredAnimationSpec) -> Optional[str]:
        """Apply pattern-specific optimizations for common educational animations.

        Args:
            spec: The animation specification

        Returns:
            Optimized Python code if pattern is recognized, None otherwise
        """
        pattern = spec.pattern_hint

        if pattern == "progressive_disclosure":
            return self._render_progressive_disclosure(spec)
        elif pattern == "equation_visual":
            return self._render_equation_visual(spec)
        elif pattern == "compare_contrast":
            return self._render_compare_contrast(spec)
        elif pattern == "transform_concept":
            return self._render_transform_concept(spec)

        return None

    def _render_generic(self, spec: StructuredAnimationSpec) -> str:
        """Generic step-by-step rendering for any animation spec.

        This is the fallback when no pattern optimization applies.

        Args:
            spec: The animation specification

        Returns:
            Python code string
        """
        code_lines = []
        code_lines.append("# Generic structured animation rendering")
        code_lines.append(f"# Concept: {spec.concept_being_taught}")
        code_lines.append("")

        # Create all objects first
        code_lines.append("# Create objects")
        for obj in spec.objects:
            obj_code = self._create_object_code(obj)
            code_lines.append(obj_code)

        code_lines.append("")
        code_lines.append("# Execute animation steps")

        # Sort steps by timestamp
        sorted_steps = sorted(spec.progression, key=lambda s: s.timestamp)

        prev_time = 0.0
        for step in sorted_steps:
            # Wait if needed
            wait_time = step.timestamp - prev_time
            if wait_time > 0:
                code_lines.append(f"self.wait({wait_time:.2f})")

            # Render the step
            step_code = self._render_step_code(step)
            code_lines.append(step_code)

            prev_time = step.timestamp

        # Wait for remaining duration
        final_wait = spec.total_duration - prev_time
        if final_wait > 0:
            code_lines.append(f"self.wait({final_wait:.2f})")

        return "\n".join(code_lines)

    def _create_object_code(self, obj: AnimationObject) -> str:
        """Generate code to create a Manim mobject from AnimationObject.

        Args:
            obj: The animation object specification

        Returns:
            Python code line creating the object
        """
        shape_class = obj.shape
        props = obj.properties

        # Handle special cases
        if obj.shape == "text":
            content = props.get("content", obj.represents)
            color = props.get("color", "WHITE")
            font_size = props.get("font_size", 36)
            return f"{obj.id} = Text('{content}', color={color}, font_size={font_size})"

        elif obj.shape == "equation":
            content = props.get("content", "")
            color = props.get("color", "WHITE")
            return f"{obj.id} = MathTex(r'{content}', color={color})"

        elif obj.shape == "circle":
            radius = props.get("radius", 0.5)
            color = props.get("color", "BLUE")
            return f"{obj.id} = Circle(radius={radius}, color={color})"

        elif obj.shape == "rectangle":
            width = props.get("width", 2.0)
            height = props.get("height", 1.0)
            color = props.get("color", "BLUE")
            return f"{obj.id} = Rectangle(width={width}, height={height}, color={color})"

        elif obj.shape == "square":
            side_length = props.get("side_length", 1.0)
            color = props.get("color", "BLUE")
            return f"{obj.id} = Square(side_length={side_length}, color={color})"

        elif obj.shape == "arrow":
            start = props.get("start", [0, 0, 0])
            end = props.get("end", [1, 0, 0])
            color = props.get("color", "RED")
            return f"{obj.id} = Arrow(start={start}, end={end}, color={color})"

        elif obj.shape == "dot":
            point = props.get("point", [0, 0, 0])
            color = props.get("color", "WHITE")
            return f"{obj.id} = Dot(point={point}, color={color})"

        elif obj.shape == "line":
            start = props.get("start", [0, 0, 0])
            end = props.get("end", [1, 0, 0])
            color = props.get("color", "WHITE")
            return f"{obj.id} = Line(start={start}, end={end}, color={color})"

        else:
            # Fallback
            return f"{obj.id} = Circle(radius=0.5, color=GRAY)  # Unknown shape: {obj.shape}"

    def _render_step_code(self, step: AnimationStep) -> str:
        """Generate code for a single animation step.

        Args:
            step: The animation step specification

        Returns:
            Python code line executing the step
        """
        action = step.action
        targets = step.targets
        params = step.params

        # Get duration from params, default to 1 second
        duration = params.get("duration", 1.0)

        # Handle different action types
        if action == "create":
            target_str = ", ".join(targets)
            return f"self.play(Create({target_str}), run_time={duration})"

        elif action == "fade_in":
            target_str = ", ".join(targets)
            return f"self.play(FadeIn({target_str}), run_time={duration})"

        elif action == "fade_out":
            target_str = ", ".join(targets)
            return f"self.play(FadeOut({target_str}), run_time={duration})"

        elif action == "write":
            target_str = ", ".join(targets)
            return f"self.play(Write({target_str}), run_time={duration})"

        elif action == "move":
            direction = params.get("direction", "RIGHT")
            distance = params.get("distance", 1.0)
            lines = []
            for target in targets:
                lines.append(f"self.play({target}.animate.shift({direction} * {distance}), run_time={duration})")
            return "\n".join(lines)

        elif action == "shift":
            vector = params.get("vector", [1, 0, 0])
            lines = []
            for target in targets:
                lines.append(f"self.play({target}.animate.shift({vector}), run_time={duration})")
            return "\n".join(lines)

        elif action == "highlight":
            target_str = ", ".join(targets)
            return f"self.play(Indicate({target_str}), run_time={duration})"

        elif action == "indicate":
            target_str = ", ".join(targets)
            return f"self.play(Indicate({target_str}), run_time={duration})"

        elif action == "focus_on":
            target_str = targets[0] if targets else "ORIGIN"
            return f"self.play(FocusOn({target_str}), run_time={duration})"

        elif action == "grow":
            target_str = ", ".join(targets)
            return f"self.play(GrowFromCenter({target_str}), run_time={duration})"

        elif action == "shrink":
            lines = []
            for target in targets:
                lines.append(f"self.play({target}.animate.scale(0.5), run_time={duration})")
            return "\n".join(lines)

        elif action == "transform" or action == "morph":
            if len(targets) >= 2:
                return f"self.play(Transform({targets[0]}, {targets[1]}), run_time={duration})"
            else:
                return f"# Cannot transform: need at least 2 targets"

        elif action == "destroy":
            target_str = ", ".join(targets)
            return f"self.play(FadeOut({target_str}), run_time={duration})"

        else:
            return f"# Unknown action: {action}"

    # ========================================================================
    # Pattern-Specific Optimizations
    # ========================================================================

    def _render_progressive_disclosure(self, spec: StructuredAnimationSpec) -> str:
        """Optimized rendering for progressive disclosure pattern.

        Progressive disclosure shows information step-by-step, building complexity.
        Common in introductory educational content.
        """
        code_lines = []
        code_lines.append("# Progressive Disclosure Pattern")
        code_lines.append(f"# Concept: {spec.concept_being_taught}")
        code_lines.append("")

        # Create all objects
        for obj in spec.objects:
            code_lines.append(self._create_object_code(obj))

        code_lines.append("")

        # Render steps with emphasis on sequential revelation
        sorted_steps = sorted(spec.progression, key=lambda s: s.timestamp)

        prev_time = 0.0
        for step in sorted_steps:
            wait_time = step.timestamp - prev_time
            if wait_time > 0:
                code_lines.append(f"self.wait({wait_time:.2f})")

            code_lines.append(self._render_step_code(step))
            prev_time = step.timestamp

        final_wait = spec.total_duration - prev_time
        if final_wait > 0:
            code_lines.append(f"self.wait({final_wait:.2f})")

        return "\n".join(code_lines)

    def _render_equation_visual(self, spec: StructuredAnimationSpec) -> str:
        """Optimized rendering for equation + visual pattern.

        Shows equation with synchronized visual representations of terms.
        Common in math/physics education (e.g., F=ma with arrows/objects).
        """
        code_lines = []
        code_lines.append("# Equation + Visual Pattern")
        code_lines.append(f"# Concept: {spec.concept_being_taught}")
        code_lines.append("")

        # Find equation objects vs visual objects
        equation_objs = [obj for obj in spec.objects if obj.shape == "equation"]
        visual_objs = [obj for obj in spec.objects if obj.shape != "equation"]

        # Create equation first
        for obj in equation_objs:
            code_lines.append(self._create_object_code(obj))

        # Create visuals
        for obj in visual_objs:
            code_lines.append(self._create_object_code(obj))

        code_lines.append("")

        # Render steps
        sorted_steps = sorted(spec.progression, key=lambda s: s.timestamp)

        prev_time = 0.0
        for step in sorted_steps:
            wait_time = step.timestamp - prev_time
            if wait_time > 0:
                code_lines.append(f"self.wait({wait_time:.2f})")

            code_lines.append(self._render_step_code(step))
            prev_time = step.timestamp

        final_wait = spec.total_duration - prev_time
        if final_wait > 0:
            code_lines.append(f"self.wait({final_wait:.2f})")

        return "\n".join(code_lines)

    def _render_compare_contrast(self, spec: StructuredAnimationSpec) -> str:
        """Optimized rendering for compare/contrast pattern.

        Shows two scenarios side-by-side to highlight differences.
        Common in comparative explanations.
        """
        code_lines = []
        code_lines.append("# Compare & Contrast Pattern")
        code_lines.append(f"# Concept: {spec.concept_being_taught}")
        code_lines.append("")

        # Create all objects with positioning
        for obj in spec.objects:
            obj_code = self._create_object_code(obj)
            code_lines.append(obj_code)

            # Apply positioning if specified
            if "position" in obj.properties:
                pos = obj.properties["position"]
                code_lines.append(f"{obj.id}.move_to({pos})")

        code_lines.append("")

        # Render steps
        sorted_steps = sorted(spec.progression, key=lambda s: s.timestamp)

        prev_time = 0.0
        for step in sorted_steps:
            wait_time = step.timestamp - prev_time
            if wait_time > 0:
                code_lines.append(f"self.wait({wait_time:.2f})")

            code_lines.append(self._render_step_code(step))
            prev_time = step.timestamp

        final_wait = spec.total_duration - prev_time
        if final_wait > 0:
            code_lines.append(f"self.wait({final_wait:.2f})")

        return "\n".join(code_lines)

    def _render_transform_concept(self, spec: StructuredAnimationSpec) -> str:
        """Optimized rendering for concept transformation pattern.

        Morphs one concept into another to show evolution/connection.
        Common in conceptual bridges and summarization.
        """
        code_lines = []
        code_lines.append("# Transform Concept Pattern")
        code_lines.append(f"# Concept: {spec.concept_being_taught}")
        code_lines.append("")

        # Create all objects
        for obj in spec.objects:
            code_lines.append(self._create_object_code(obj))

        code_lines.append("")

        # Render steps with emphasis on transforms
        sorted_steps = sorted(spec.progression, key=lambda s: s.timestamp)

        prev_time = 0.0
        for step in sorted_steps:
            wait_time = step.timestamp - prev_time
            if wait_time > 0:
                code_lines.append(f"self.wait({wait_time:.2f})")

            code_lines.append(self._render_step_code(step))
            prev_time = step.timestamp

        final_wait = spec.total_duration - prev_time
        if final_wait > 0:
            code_lines.append(f"self.wait({final_wait:.2f})")

        return "\n".join(code_lines)


def render_structured_animation(spec: StructuredAnimationSpec) -> str:
    """Convenience function to render a StructuredAnimationSpec.

    Args:
        spec: The structured animation specification

    Returns:
        Python code string ready to execute in Manim Scene
    """
    renderer = AnimationRenderer()
    return renderer.render(spec)
