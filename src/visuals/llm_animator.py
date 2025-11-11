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

## 3Blue1Brown Educational Philosophy

You are creating animations in the style of 3Blue1Brown - the gold standard for mathematical visualization. Follow these core principles:

### 1. Progressive Disclosure (MOST IMPORTANT)
**Never show everything at once.** Build understanding step by step:
- Start with the simplest element
- Add one piece of complexity at a time
- Each animation adds ONE new insight
- Keep previous elements visible as you add new ones

**Example: Teaching F=ma**
```python
# ❌ BAD: Show everything at once
car = Rectangle(...)
force_arrow = Arrow(...)
equation = MathTex("F = ma")
self.play(FadeIn(VGroup(car, force_arrow, equation)))  # Too much!

# ✅ GOOD: Progressive disclosure
# Step 1: Introduce the object
car = Rectangle(width=2, height=1, color=BLUE, fill_opacity=0.8)
self.play(Create(car), run_time=0.8)

# Step 2: Add the force
force_arrow = Arrow(car.get_left(), car.get_left() + LEFT*1.5, color=RED, buff=0)
self.play(Create(force_arrow), run_time=0.7)

# Step 3: Show the effect (acceleration)
self.play(car.animate.shift(RIGHT*3), run_time=1.5)
```

### 2. Visual Continuity
**Objects should transform and evolve, not disappear and reappear:**
- Use `Transform` and `ReplacementTransform` to morph concepts
- Keep elements on screen and build on them
- Create narrative flow: "this becomes that"

### 3. Color as Semantic Meaning
**Colors represent concepts, not just decoration:**
- `BLUE` = Primary concept/object being studied
- `RED` = Forces, energy, important relationships
- `GREEN` = Examples, specific instances
- `YELLOW` = Highlights, attention focus
- `WHITE` = Equations, formulas
- Use the SAME color for the SAME concept throughout

### 4. Mathematical Correspondence
**Visuals should directly relate to equation terms:**
- Color-code equation terms to match their visual representations
- Point to/highlight specific terms while showing their meaning
- Animations of visuals should mirror animations of equations

## Code Structure

1. **No class or function definitions** - Just write the animation code directly
2. **Use `self`** - You have access to `self.play()`, `self.add()`, etc.
3. **Duration Control**:
   - Use `run_time` parameter in `self.play()` calls
   - **DO NOT use `self.wait()`** - duration timing is handled automatically
   - Focus on animation timing, not total duration
4. **Progressive Building**: Build scenes step-by-step, don't show everything at once
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

**Colors** (Use semantically!):
- `BLUE` - Primary concept/object
- `RED` - Forces, energy, relationships
- `GREEN` - Examples, specific instances
- `YELLOW` - Highlights, attention
- `ORANGE`, `PURPLE`, `PINK` - Secondary elements
- `GRAY`, `DARK_GRAY`, `LIGHT_GRAY` - Background elements
- `WHITE` - Equations, neutral
- `BLACK` - Background (rarely used)

**VGroup (Critical for Complex Scenes)**:
```python
# Create complex scene by grouping
car = Rectangle(...)
arrow = Arrow(...)
label = Text("Force")

# Group them together
scene = VGroup(car, arrow, label)

# Arrange spatially
scene.arrange(DOWN, buff=0.5)  # Stack vertically
# OR
scene.arrange(RIGHT, buff=1)  # Arrange horizontally

# Animate as a unit
self.play(FadeIn(scene))
self.play(scene.animate.shift(UP*2))

# Or animate individually after grouping
self.play(
    FadeIn(car),
    FadeIn(arrow),
    FadeIn(label),
    run_time=1.2
)
```

## Animation Control & Advanced Techniques

**Basic Control**:
- `self.play(animation, run_time=2.0)` - play animation with specific duration
- `self.add(mobject)` - add to scene without animation
- `self.remove(mobject)` - remove from scene

**Transform (Visual Continuity)**:
```python
# Transform: Morph one object into another (keeps original object)
circle = Circle(color=BLUE)
square = Square(color=RED)

self.play(Create(circle), run_time=0.8)
self.play(Transform(circle, square), run_time=1.2)
# circle now looks like square, but `circle` variable still exists

# ReplacementTransform: Remove old, add new
concept_text = Text("General Idea")
specific_text = Text("Specific Example")

self.play(Write(concept_text), run_time=1.0)
self.play(ReplacementTransform(concept_text, specific_text), run_time=1.2)
# concept_text is now gone, specific_text is on screen
```

**Indicate & FocusOn (Drawing Attention)**:
```python
# Indicate: Briefly highlight/emphasize an object
equation = MathTex("F", "=", "m", "a").to_edge(UP)
self.play(Write(equation))

# Highlight the 'F' term
self.play(Indicate(equation[0], color=YELLOW), run_time=0.8)

# Or use FocusOn for a spotlight effect
self.play(FocusOn(equation[2]), run_time=0.5)  # Focus on 'm'
```

**Simultaneous Animations (Natural Pacing)**:
```python
# Overlap animations for smooth transitions
old_obj = Circle(color=BLUE)
new_obj = Square(color=RED).shift(RIGHT*2)

self.play(Create(old_obj), run_time=0.8)

# Fade out old while fading in new (no gap!)
self.play(
    FadeOut(old_obj, shift=LEFT),
    FadeIn(new_obj, shift=LEFT),
    run_time=1.2
)
```

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

## Educational Animation Patterns (3Blue1Brown Style)

These are proven patterns for teaching concepts visually. Use these as templates:

### Pattern 1: Introduce → Elaborate → Apply (Progressive Disclosure)
**Best for: Introducing new concepts**

```python
# Step 1: Introduce (simple)
obj = Circle(radius=0.8, color=BLUE, fill_opacity=0.8)
self.play(Create(obj), run_time=0.8)

# Step 2: Elaborate (add context)
label = Text("Mass").scale(0.7).next_to(obj, UP)
self.play(Write(label), run_time=0.7)

# Step 3: Apply (show in action)
force = Arrow(obj.get_left(), obj.get_left() + LEFT, color=RED, buff=0)
self.play(Create(force), run_time=0.6)
self.play(obj.animate.shift(RIGHT*3), run_time=1.5)
```

### Pattern 2: Equation → Visual → Example (Mathematical Correspondence)
**Best for: Explaining formulas**

```python
# Step 1: Show equation
equation = MathTex("F", "=", "m", "a").to_edge(UP)
equation[0].set_color(RED)    # Force
equation[2].set_color(BLUE)   # Mass
equation[3].set_color(GREEN)  # Acceleration
self.play(Write(equation), run_time=1.2)

# Step 2: Visual for each term
mass = Circle(radius=0.5, color=BLUE, fill_opacity=0.8)
mass.shift(DOWN + LEFT*2)

self.play(Indicate(equation[2], color=YELLOW), run_time=0.5)  # Highlight 'm'
self.play(FadeIn(mass), run_time=0.7)  # Show corresponding visual

# Step 3: Show relationship
force_arrow = Arrow(mass.get_left(), mass.get_left() + LEFT, color=RED)
self.play(
    Indicate(equation[0], color=YELLOW),
    Create(force_arrow),
    run_time=0.8
)

# Step 4: Show result (acceleration)
self.play(
    Indicate(equation[3], color=YELLOW),
    mass.animate.shift(RIGHT*2.5),
    run_time=1.3
)
```

### Pattern 3: Transform Concept (Visual Continuity)
**Best for: Showing relationships between ideas**

```python
# Start with general idea
general = Text("Objects resist change").scale(0.8)
self.play(Write(general), run_time=1.0)

# Morph to specific law
specific = Text("Newton's First Law").scale(0.9)
self.play(ReplacementTransform(general, specific), run_time=1.2)

# Morph to equation
equation = MathTex(r"\vec{v} = \text{constant when } \sum \vec{F} = 0")
self.play(ReplacementTransform(specific, equation), run_time=1.3)
```

### Pattern 4: Compare & Contrast (Simultaneous Display)
**Best for: Showing differences**

```python
# Set up two scenarios side by side
# Scenario 1: With friction
friction_scene = VGroup(
    Rectangle(width=1, height=0.6, color=BLUE, fill_opacity=0.8),
    Text("With Friction").scale(0.5)
).arrange(DOWN).shift(LEFT*2.5)

# Scenario 2: Without friction
no_friction_scene = VGroup(
    Rectangle(width=1, height=0.6, color=GREEN, fill_opacity=0.8),
    Text("No Friction").scale(0.5)
).arrange(DOWN).shift(RIGHT*2.5)

# Show both at once
self.play(
    FadeIn(friction_scene),
    FadeIn(no_friction_scene),
    run_time=1.0
)

# Animate differently
self.play(
    friction_scene[0].animate.shift(DOWN*0.5),  # Slow/stop
    no_friction_scene[0].animate.shift(DOWN*2),  # Keep going
    run_time=2.0
)
```

❌ **DON'T**: Make complex multi-part objects
✅ **DO**: Use single simple shapes

## Common Patterns

**Object moving across screen**:
```python
obj = Circle(color=BLUE, fill_opacity=0.8)
obj.shift(LEFT * 4)
self.play(FadeIn(obj), run_time=0.7)
self.play(obj.animate.shift(RIGHT * 8), run_time=2.8)
```

**Text appearing then disappearing**:
```python
text = Text("Hello World", font_size=48)
self.play(Write(text), run_time=1.5)
self.play(FadeOut(text), run_time=1.0)
```

**Shape transformation**:
```python
circle = Circle(color=BLUE, fill_opacity=0.7)
square = Square(color=RED, fill_opacity=0.7)
self.play(Create(circle), run_time=1.2)
self.play(Transform(circle, square), run_time=1.8)
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

        # Add deterministic duration control
        code = add_deterministic_duration(code, duration)

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


def add_deterministic_duration(code: str, target_duration: float) -> str:
    """Add deterministic wait() to match target duration.

    Parses all run_time parameters, calculates total animation time,
    and adds a wait() call for remaining duration.

    Args:
        code: Generated animation code
        target_duration: Target duration in seconds

    Returns:
        Code with deterministic wait() appended

    Example:
        >>> code = "self.play(FadeIn(obj), run_time=1.5)\\nself.play(obj.animate.shift(RIGHT*3), run_time=2.0)"
        >>> add_deterministic_duration(code, 4.0)
        # Returns code with "self.wait(0.5)" appended
    """
    import re

    # Find all run_time values using regex
    # Matches: run_time=1.5, run_time = 2.0, run_time= 3
    run_time_pattern = r'run_time\s*=\s*([\d.]+)'
    matches = re.findall(run_time_pattern, code)

    # Calculate total animation time
    total_animation_time = sum(float(t) for t in matches)

    # Calculate remaining time
    remaining = target_duration - total_animation_time

    logger.debug(f"Animation time: {total_animation_time:.2f}s, Target: {target_duration:.2f}s, Remaining: {remaining:.2f}s")

    # Add wait if we have significant remaining time
    # Minimum threshold of 0.1s to avoid tiny waits
    if remaining > 0.1:
        code = code.rstrip() + f"\nself.wait({remaining:.2f})"
        logger.debug(f"Added wait({remaining:.2f}s)")
    elif remaining < -0.1:
        # Animation is longer than target - log warning but don't error
        logger.warning(f"Animation time ({total_animation_time:.2f}s) exceeds target ({target_duration:.2f}s)")

    return code


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
