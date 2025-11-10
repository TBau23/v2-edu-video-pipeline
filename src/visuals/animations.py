"""
Reusable animation primitives for physics and math education.

This module provides a library of common animations that can be referenced
in VisualSpecs. The goal is to build meaningful, pedagogically useful animations,
not just placeholder graphics.

Each animation should:
1. Be parameterizable (velocity, direction, color, etc.)
2. Have clear visual purpose (teaching a concept)
3. Be composable (can be combined with other elements)
"""

from manim import *
import numpy as np


class PhysicsAnimations:
    """Collection of physics-related animations."""

    @staticmethod
    def car_accelerating(
        start_pos=LEFT * 4,
        end_pos=RIGHT * 4,
        acceleration=1.0,
        duration=3.0,
        show_motion_lines=True,
        **kwargs
    ):
        """Create a car that accelerates from rest.

        Args:
            start_pos: Starting position
            end_pos: Ending position
            acceleration: Acceleration factor (visual)
            duration: Animation duration
            show_motion_lines: Whether to show motion lines

        Returns:
            VGroup containing car and animations
        """
        # Simple car: rectangle body + circular wheels
        body = Rectangle(width=1.5, height=0.6, fill_opacity=1, fill_color=BLUE)
        wheel1 = Circle(radius=0.2, fill_opacity=1, fill_color=DARK_GRAY)
        wheel2 = Circle(radius=0.2, fill_opacity=1, fill_color=DARK_GRAY)

        wheel1.next_to(body, DOWN, buff=0).shift(LEFT * 0.4)
        wheel2.next_to(body, DOWN, buff=0).shift(RIGHT * 0.4)

        car = VGroup(body, wheel1, wheel2)
        car.move_to(start_pos)

        # Create rate function for acceleration (starts slow, speeds up)
        def accelerate_rate(t):
            return t ** (1 + acceleration)

        animations = [
            car.animate(rate_func=accelerate_rate).move_to(end_pos)
        ]

        # TODO: Add motion lines if requested

        return car, animations, duration

    @staticmethod
    def hockey_puck_sliding(
        start_pos=LEFT * 4,
        end_pos=RIGHT * 4,
        velocity=2.0,
        duration=3.0,
        show_motion_lines=True,
        **kwargs
    ):
        """Hockey puck moving at constant velocity.

        Demonstrates Newton's First Law - constant motion without force.
        """
        # Puck: flat cylinder (disk)
        puck = Circle(radius=0.3, fill_opacity=1, fill_color=GRAY)
        puck.set_stroke(DARK_GRAY, width=2)
        puck.move_to(start_pos)

        # Ice surface (subtle)
        ice = Rectangle(
            width=10,
            height=0.1,
            fill_opacity=0.3,
            fill_color=BLUE_E
        ).shift(DOWN * 0.5)

        # Constant velocity motion
        animations = [
            puck.animate(rate_func=linear).move_to(end_pos)
        ]

        group = VGroup(ice, puck)

        return group, animations, duration

    @staticmethod
    def object_at_rest(
        obj_type="book",
        show_forces=False,
        **kwargs
    ):
        """Object at rest on a surface.

        Args:
            obj_type: "book", "ball", "box"
            show_forces: Whether to show force arrows
        """
        if obj_type == "book":
            obj = Rectangle(width=1.0, height=0.6, fill_opacity=1, fill_color=MAROON_B)
        elif obj_type == "ball":
            obj = Circle(radius=0.4, fill_opacity=1, fill_color=RED)
        else:  # box
            obj = Square(side_length=0.8, fill_opacity=1, fill_color=ORANGE)

        # Surface
        surface = Line(LEFT * 5, RIGHT * 5, color=GRAY)
        obj.next_to(surface, UP, buff=0)

        group = VGroup(surface, obj)

        # Force arrows if requested
        if show_forces:
            # Weight (downward)
            weight = Arrow(
                start=obj.get_center(),
                end=obj.get_center() + DOWN * 1.5,
                color=RED,
                buff=0
            )
            weight_label = Text("mg", font_size=24).next_to(weight, RIGHT, buff=0.1)

            # Normal force (upward)
            normal = Arrow(
                start=obj.get_center(),
                end=obj.get_center() + UP * 1.5,
                color=BLUE,
                buff=0
            )
            normal_label = Text("N", font_size=24).next_to(normal, RIGHT, buff=0.1)

            group.add(weight, weight_label, normal, normal_label)

        animations = [FadeIn(group)]
        duration = 2.0

        return group, animations, duration

    @staticmethod
    def person_in_braking_car(
        duration=3.0,
        **kwargs
    ):
        """Person lurching forward when car brakes.

        Demonstrates inertia - body wants to continue moving.
        """
        # Simplified car interior
        car = Rectangle(width=3, height=2, color=WHITE)

        # Person (stick figure)
        head = Circle(radius=0.2, fill_opacity=1, fill_color=YELLOW)
        body_line = Line(ORIGIN, DOWN * 0.8)
        person = VGroup(head, body_line)

        # Position person in car (upright initially)
        person.move_to(car.get_center()).shift(LEFT * 0.5)

        group = VGroup(car, person)

        # Animation: car decelerates, person continues forward (leans)
        # This is simplified - real version would use proper rotation
        animations = [
            person.animate.shift(RIGHT * 0.5 + DOWN * 0.2)
        ]

        return group, animations, duration


class MathAnimations:
    """Collection of math-related animations."""

    @staticmethod
    def equation_progressive_reveal(
        equation_parts: list[str],
        duration=2.0,
        **kwargs
    ):
        """Reveal equation parts progressively.

        Args:
            equation_parts: List of LaTeX strings to reveal in sequence
            duration: Total duration

        Example:
            ["F", "= m", "a"] → reveals F, then = m, then a
        """
        equations = [MathTex(part) for part in equation_parts]

        # Position them to align properly
        full_eq = MathTex("".join(equation_parts))
        for i, eq in enumerate(equations):
            if i == 0:
                eq.move_to(full_eq.get_left() + RIGHT * eq.width / 2)
            else:
                eq.next_to(equations[i - 1], RIGHT, buff=0.1)

        # Animations: write each part in sequence
        animations = []
        part_duration = duration / len(equations)

        for eq in equations:
            # Note: Renderer will need to handle run_time for each animation
            # For now, return animation objects without timing tuples
            animations.append(Write(eq, run_time=part_duration))

        return VGroup(*equations), animations, duration

    @staticmethod
    def function_plot_animated(
        func,
        x_range=[-5, 5],
        y_range=[-5, 5],
        duration=3.0,
        **kwargs
    ):
        """Animate drawing a function plot.

        Args:
            func: Function to plot (as lambda or string)
            x_range: [min, max, step]
            y_range: [min, max, step]
            duration: Animation duration
        """
        axes = Axes(
            x_range=x_range,
            y_range=y_range,
            x_length=6,
            y_length=4,
        )

        # Convert string to lambda if needed
        if isinstance(func, str):
            func = lambda x: eval(func)

        graph = axes.plot(func, color=BLUE)

        group = VGroup(axes, graph)

        animations = [
            Create(axes),
            Create(graph)
        ]

        return group, animations, duration


class AnimationLibrary:
    """Central registry of all available animations.

    This allows VisualSpecs to reference animations by name.
    """

    _registry = {
        # Physics
        "car_accelerating": PhysicsAnimations.car_accelerating,
        "hockey_puck_sliding": PhysicsAnimations.hockey_puck_sliding,
        "object_at_rest": PhysicsAnimations.object_at_rest,
        "person_in_braking_car": PhysicsAnimations.person_in_braking_car,

        # Math
        "equation_progressive_reveal": MathAnimations.equation_progressive_reveal,
        "function_plot_animated": MathAnimations.function_plot_animated,
    }

    @classmethod
    def get_animation(cls, name: str):
        """Get animation function by name.

        Args:
            name: Animation name

        Returns:
            Animation function

        Raises:
            KeyError: If animation not found
        """
        if name not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise KeyError(
                f"Animation '{name}' not found. Available: {available}"
            )

        return cls._registry[name]

    @classmethod
    def list_animations(cls) -> list[str]:
        """List all available animations."""
        return list(cls._registry.keys())

    @classmethod
    def register(cls, name: str, func):
        """Register a new animation.

        Args:
            name: Animation name
            func: Animation function
        """
        cls._registry[name] = func
