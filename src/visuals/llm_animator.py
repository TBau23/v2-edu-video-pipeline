"""
LLM-powered Manim animation code generator.

This module uses an LLM (GPT-4) to generate executable Manim Scene code
from natural language descriptions. This allows for unlimited flexibility
in animation creation without manually coding each animation type.
"""

import os
import sys
import logging
import importlib.util
import tempfile
from pathlib import Path
from typing import Optional
from openai import OpenAI

from src.visuals.executor import SceneExecutor

logger = logging.getLogger(__name__)


# System prompt for generating inline animation code
MANIM_INLINE_ANIMATION_PROMPT = """You are an expert Manim animator. Your job is to generate Python code snippets that create and animate Manim objects.

## Your Task

Generate executable Python code that creates Manim objects and animates them. The code will be executed inside an existing Scene's construct() method, so you have access to `self` (the Scene instance).

**IMPORTANT**: Do NOT create a class or def construct(). Just write the animation code directly.

## Code Structure

1. **No class or function definitions** - Just write the animation code directly
2. **Use `self`** - You have access to `self.play()`, `self.wait()`, `self.add()`, etc.
3. **Duration Control**: Use `self.wait()` and animation `run_time` parameters to match target duration
4. **Simplicity**: Keep animations simple and clear - complex scenes often fail to render
5. **Direct execution**: Code will be executed with exec() in the scene context

## Available Manim Components

**Shapes & Objects**:
- `Circle(radius=1, color=BLUE, fill_opacity=0.5)`
- `Square(side_length=2, color=RED)`
- `Rectangle(width=3, height=2, color=GREEN)`
- `Triangle(color=YELLOW)`
- `Dot(point=ORIGIN, color=WHITE)`
- `Arrow(start=LEFT, end=RIGHT, color=RED)`
- `Line(start=LEFT*3, end=RIGHT*3, color=BLUE)`

**Text & Math**:
- `Text("Hello", font_size=48, color=WHITE)`
- `MathTex(r"E = mc^2", font_size=48)` (for LaTeX equations)

**Animations**:
- `FadeIn(mobject)` - fade in
- `FadeOut(mobject)` - fade out
- `Write(text)` - write text/equation
- `Create(shape)` - draw shape
- `Transform(mobject1, mobject2)` - morph one into another
- `mobject.animate.shift(direction)` - move object
- `mobject.animate.scale(factor)` - resize object
- `mobject.animate.rotate(angle)` - rotate object

**Positioning**:
- `UP`, `DOWN`, `LEFT`, `RIGHT` - cardinal directions (unit vectors)
- `ORIGIN` - center of screen [0, 0, 0]
- `mobject.shift(UP*2 + RIGHT*3)` - move by vector
- `mobject.move_to(position)` - move to absolute position
- `mobject.next_to(other, direction)` - position relative to another object
- `mobject.to_edge(UP)` - move to screen edge

**Colors**:
- `BLUE`, `RED`, `GREEN`, `YELLOW`, `ORANGE`, `PURPLE`, `PINK`
- `GRAY`, `DARK_GRAY`, `LIGHT_GRAY`
- `WHITE`, `BLACK`

**Grouping**:
- `VGroup(obj1, obj2, obj3)` - group objects together

## Animation Control

- `self.play(animation, run_time=2.0)` - play animation with specific duration
- `self.wait(1.5)` - pause for time
- `self.add(mobject)` - add to scene without animation
- `self.remove(mobject)` - remove from scene

## Important Guidelines

1. **KEEP IT EXTREMELY SIMPLE**: Manim is for abstract, geometric education videos
   - A car = a single Rectangle or Square, NOT body+wheels
   - A person = a Circle or Dot
   - A ball = a Circle
   - Don't try to make realistic objects with multiple parts
   - Abstract is BETTER than detailed

2. **Duration Matching**: If target duration is 4 seconds, the total time of all animations and waits should sum to ~4 seconds

3. **Run Time**: Use `run_time` parameter in `self.play()` to control individual animation speeds

4. **Object Creation**: Create objects before animating them

5. **Visual Clarity**: Use appropriate colors, sizes, and positioning for educational clarity

6. **Motion**: Use `.animate` for smooth transformations

**Remember: Simple geometric shapes are more effective for education than complex realistic drawings. A car is just a rectangle. A person is just a circle. Keep it abstract.**

## Example Code

Here's a reference for good, SIMPLE inline animation code:

```python
# Simple circle moving across screen
circle = Circle(radius=1, color=BLUE, fill_opacity=0.5)
circle.shift(LEFT * 3)

self.play(FadeIn(circle), run_time=1.0)
self.play(circle.animate.shift(RIGHT * 6), run_time=2.0)
self.wait(1.0)
```

## Example: Car Accelerating (CORRECT - SIMPLE)
```python
# Car = just a rectangle, nothing more!
car = Rectangle(width=1.5, height=0.8, color=BLUE, fill_opacity=0.8)
car.shift(LEFT * 4)

# Simple animation
self.play(FadeIn(car), run_time=0.5)
self.play(car.animate.shift(RIGHT * 8), run_time=3.0, rate_func=smooth)
self.wait(0.5)
```

❌ **DON'T**: Make complex multi-part objects
✅ **DO**: Use single simple shapes

## Common Patterns

**Object moving across screen**:
```python
obj = Circle(color=BLUE)
obj.shift(LEFT * 4)
self.play(FadeIn(obj), run_time=0.5)
self.play(obj.animate.shift(RIGHT * 8), run_time=3.0)
self.wait(0.5)
```

**Text appearing then disappearing**:
```python
text = Text("Hello World", font_size=48)
self.play(Write(text), run_time=1.0)
self.wait(2.0)
self.play(FadeOut(text), run_time=0.5)
```

**Shape transformation**:
```python
circle = Circle(color=BLUE)
square = Square(color=RED)
self.play(Create(circle), run_time=1.0)
self.wait(0.5)
self.play(Transform(circle, square), run_time=1.5)
self.wait(1.0)
```

## Output Format

Generate ONLY the Python code, with no explanations, markdown formatting, or extra text. The code should be immediately executable in a Scene's construct() method.

Do NOT include:
- `from manim import *` (already imported)
- `class` definitions
- `def construct(self):`

Just write the animation code directly starting with object creation.
"""


def generate_animation_scene(
    description: str,
    duration: float,
    api_key: Optional[str] = None,
    model: str = "gpt-4o"
) -> str:
    """Generate Manim Scene code from natural language description.

    Uses GPT-4 to generate a complete, executable Manim Scene class that
    animates the described concept.

    Args:
        description: Natural language description of what to animate
                    Example: "A blue car accelerating from left to right"
        duration: Target duration for the animation in seconds
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        model: OpenAI model to use (default: gpt-4o)

    Returns:
        Python code string containing a Scene class definition

    Raises:
        ValueError: If API key is missing
        Exception: If code generation fails

    Example:
        >>> code = generate_animation_scene(
        ...     "A red circle moving across the screen",
        ...     duration=3.0
        ... )
        >>> print(code)
        from manim import *

        class GeneratedAnimation(Scene):
            def construct(self):
                circle = Circle(radius=1, color=RED)
                ...
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key required. Set OPENAI_API_KEY environment variable "
            "or pass api_key parameter."
        )

    logger.info(f"Generating animation code for: {description[:50]}...")
    logger.info(f"Target duration: {duration}s")

    # Create OpenAI client
    client = OpenAI(api_key=api_key)

    # Construct user message
    user_message = f"""Create inline Manim animation code for the following:

{description}

Target duration: {duration} seconds

Important: Generate ONLY the Python code, no markdown code blocks, no explanations, no class or function definitions.
Just write the animation code that can be executed directly in a Scene's construct() method."""

    try:
        # Call OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": MANIM_INLINE_ANIMATION_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        # Extract code from response
        code = response.choices[0].message.content.strip()

        # Clean up code (remove markdown formatting if present)
        code = _clean_generated_code(code)

        # Validate code structure for inline code
        _validate_inline_code(code)

        logger.info("✓ Animation code generated successfully")
        logger.debug(f"Generated code:\n{code}")

        return code

    except Exception as e:
        logger.error(f"Animation code generation failed: {e}")
        raise Exception(f"Failed to generate animation code: {e}") from e


def _clean_generated_code(code: str) -> str:
    """Clean up generated code by removing markdown formatting.

    Args:
        code: Raw code from LLM response

    Returns:
        Cleaned Python code
    """
    # Remove markdown code blocks if present
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    elif code.startswith("```"):
        code = code[len("```"):].strip()

    if code.endswith("```"):
        code = code[:-len("```")].strip()

    return code


def _validate_scene_code(code: str) -> None:
    """Validate that generated code has correct structure.

    Args:
        code: Python code to validate

    Raises:
        ValueError: If code structure is invalid
    """
    required_patterns = [
        ("class GeneratedAnimation", "Scene class definition"),
        ("def construct(self)", "construct() method"),
        ("from manim", "Manim imports")
    ]

    for pattern, description in required_patterns:
        if pattern not in code:
            raise ValueError(
                f"Generated code missing required {description}: '{pattern}'"
            )

    # Check for dangerous operations (basic safety check)
    dangerous_operations = [
        "os.system", "subprocess", "eval(", "__import__",
        "open(", "file(", "exec("
    ]

    for danger in dangerous_operations:
        if danger in code:
            raise ValueError(
                f"Generated code contains dangerous operation: {danger}"
            )

    logger.debug("✓ Code validation passed")


def _validate_inline_code(code: str) -> None:
    """Validate that generated inline code has correct structure.

    Args:
        code: Python code to validate

    Raises:
        ValueError: If code structure is invalid
    """
    # Check for dangerous operations (basic safety check)
    dangerous_operations = [
        "os.system", "subprocess", "eval(", "__import__",
        "open(", "file(", "exec("
    ]

    for danger in dangerous_operations:
        if danger in code:
            raise ValueError(
                f"Generated code contains dangerous operation: {danger}"
            )

    # Should contain some Manim objects
    has_manim_objects = any([
        "Circle" in code,
        "Square" in code,
        "Rectangle" in code,
        "Text" in code,
        "Dot" in code,
        "Arrow" in code,
        "Line" in code,
        "self.play" in code,
        "self.add" in code
    ])

    if not has_manim_objects:
        raise ValueError(
            "Generated code doesn't appear to contain Manim objects or animations"
        )

    logger.debug("✓ Inline code validation passed")


def execute_animation_code(
    code: str,
    output_name: str,
    output_dir: Path,
    quality: str = "low_quality"
) -> Path:
    """Execute generated Manim Scene code and render to video.

    Takes generated Python code, executes it safely, and renders the
    animation using the Scene Executor.

    Args:
        code: Python code containing GeneratedAnimation Scene class
        output_name: Name for output file (without extension)
        output_dir: Directory to save rendered video
        quality: Manim quality flag ('low_quality', 'medium_quality', 'high_quality')

    Returns:
        Path to rendered video file

    Raises:
        ValueError: If code validation fails
        RuntimeError: If execution or rendering fails

    Example:
        >>> code = generate_animation_scene("A blue circle", 3.0)
        >>> video_path = execute_animation_code(
        ...     code, "my_animation", Path("output")
        ... )
        >>> print(video_path)
        output/my_animation.mp4
    """
    logger.info(f"Executing animation code: {output_name}")

    # Validate code structure first
    _validate_scene_code(code)

    # Create temp file for code
    temp_file = None

    try:
        # Write code to temporary Python file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir=tempfile.gettempdir()
        ) as f:
            f.write(code)
            temp_file = Path(f.name)

        logger.debug(f"Wrote code to temp file: {temp_file}")

        # Import the module dynamically
        spec = importlib.util.spec_from_file_location(
            "generated_animation",
            temp_file
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Failed to load module from {temp_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules['generated_animation'] = module
        spec.loader.exec_module(module)

        # Extract the Scene class
        if not hasattr(module, 'GeneratedAnimation'):
            raise RuntimeError(
                "Module does not contain 'GeneratedAnimation' class"
            )

        scene_class = module.GeneratedAnimation

        logger.debug(f"Extracted Scene class: {scene_class}")

        # Use SceneExecutor to render
        executor = SceneExecutor(output_dir, quality=quality)
        output_path = executor.render_scene(
            scene_class,
            output_name=output_name,
            preview=False
        )

        logger.info(f"✓ Animation rendered: {output_path}")

        return output_path

    except Exception as e:
        logger.error(f"Animation execution failed: {e}")
        logger.debug(f"Code that failed:\n{code}")
        raise RuntimeError(f"Failed to execute animation code: {e}") from e

    finally:
        # Clean up temp file
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
                logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")

        # Clean up module from sys.modules
        if 'generated_animation' in sys.modules:
            del sys.modules['generated_animation']


# Example usage for testing
if __name__ == "__main__":
    import sys

    # Test generation
    test_descriptions = [
        ("A blue circle moving from left to right", 3.0),
        ("A car accelerating with motion lines", 4.0),
        ("Two circles colliding and bouncing apart", 3.0),
    ]

    for description, duration in test_descriptions:
        print(f"\n{'='*60}")
        print(f"Generating: {description}")
        print(f"Duration: {duration}s")
        print('='*60)

        try:
            code = generate_animation_scene(description, duration)
            print(code)
            print("\n✓ Success!")

        except Exception as e:
            print(f"\n✗ Failed: {e}")
            sys.exit(1)
