# ANIM-001: LLM Animation Code Generator

**Priority**: P0 - Critical Path
**Estimate**: 2 hours
**Dependencies**: None
**Status**: 🔴 Not Started

---

## Goal

Create an LLM-powered code generator that takes animation descriptions and produces executable Manim Scene code.

---

## Why This Matters

This is the foundation of the LLM animation approach. Without reliable code generation, the entire system fails. This replaces the AnimationLibrary with dynamic generation.

---

## Current State

- We have AnimationLibrary with predefined animations
- Script generator creates animation VisualSpecs
- Renderer expects animation functions that return (mobject, animations, duration)

---

## Tasks

### 1. Create Module Structure (15 min)
- [ ] Create `src/visuals/llm_animator.py`
- [ ] Add docstrings explaining purpose
- [ ] Import OpenAI client
- [ ] Add logging setup

### 2. Design System Prompt (45 min)
- [ ] Research Manim best practices for video generation
- [ ] Write prompt that teaches LLM about Manim Scene structure
- [ ] Include examples of good animation code
- [ ] Add constraints (duration, safety, simplicity)
- [ ] Test prompt with various descriptions manually

**Prompt must include**:
- Manim Scene class structure
- How to use construct() method
- Duration control (self.wait() for timing)
- Common mobjects (Circle, Rectangle, Text, etc.)
- Animation types (FadeIn, Write, Create, Transform)
- Position control (UP, DOWN, LEFT, RIGHT)
- Examples of simple but effective animations

### 3. Implement Generator Function (45 min)
- [ ] `generate_animation_scene(description: str, duration: float) -> str`
- [ ] Construct user message with description + duration
- [ ] Call OpenAI with system + user prompts
- [ ] Parse response to extract code
- [ ] Validate code structure (has Scene class, construct method)
- [ ] Return code as string

**Function signature**:
```python
def generate_animation_scene(
    description: str,
    duration: float,
    api_key: Optional[str] = None,
    model: str = "gpt-4o"
) -> str:
    """Generate Manim Scene code from description.

    Args:
        description: What to animate (e.g., "A car accelerating")
        duration: Target duration in seconds
        api_key: OpenAI API key
        model: OpenAI model to use

    Returns:
        Python code string with Scene class definition

    Raises:
        ValueError: If API key missing
        Exception: If generation fails
    """
```

### 4. Add Error Handling (15 min)
- [ ] Handle OpenAI API errors
- [ ] Validate generated code structure
- [ ] Helpful error messages
- [ ] Logging for debugging

---

## Acceptance Criteria

✅ **Must have**:
- Function generates valid Python code
- Code contains a Scene class with construct() method
- Code uses Manim imports correctly
- Can generate code for simple animations (shapes, motion)
- Duration parameter is incorporated
- Errors are caught and logged

✅ **Nice to have**:
- Code is well-formatted and readable
- Includes comments explaining what it does
- Uses modern Manim API (not legacy)

---

## Test Strategy

### Manual Testing
Test with various descriptions:
- "A blue circle moving from left to right"
- "A car accelerating from rest"
- "Two balls colliding"
- "A graph showing y = x^2"

Expected: Valid Manim Scene code for each

### Unit Test
```python
def test_generate_animation_scene():
    """Test basic code generation."""
    code = generate_animation_scene(
        description="A red square fading in",
        duration=2.0
    )

    # Verify code structure
    assert "class" in code
    assert "Scene" in code
    assert "def construct(self)" in code
    assert "from manim import" in code
```

---

## Implementation Notes

### System Prompt Structure

```
You are an expert Manim animator. Generate Python code for a Manim Scene class based on descriptions.

## Requirements:
1. Create a Scene class that inherits from Scene
2. Implement construct() method with animation logic
3. Use self.play() to animate objects
4. Use self.wait() to control timing
5. Target duration should be {duration} seconds
6. Keep animations simple and clear

## Available Manim Components:
- Shapes: Circle, Square, Rectangle, Triangle
- Text: Text, MathTex (for equations)
- Animations: FadeIn, FadeOut, Write, Create, Transform
- Positions: UP, DOWN, LEFT, RIGHT, ORIGIN
- Colors: BLUE, RED, GREEN, YELLOW, etc.

## Example:
```python
from manim import *

class GeneratedAnimation(Scene):
    def construct(self):
        # Create a circle
        circle = Circle(radius=1, color=BLUE)
        circle.shift(LEFT * 3)

        # Animate
        self.play(FadeIn(circle))
        self.play(circle.animate.shift(RIGHT * 6), run_time=2.0)
        self.wait(0.5)
```

## Important:
- Class name must be "GeneratedAnimation"
- Total runtime should match target duration
- Use run_time parameter to control animation speed
- Keep it simple - complex animations often fail
```

### User Message Template

```
Create a Manim Scene that animates the following:

{description}

Target duration: {duration} seconds

Generate ONLY the Python code, no explanations.
```

---

## Blockers / Risks

**Risk**: LLM generates invalid Manim syntax
- **Mitigation**: Include examples in prompt, validate structure
- **Fallback**: Try again with different prompt

**Risk**: Generated code uses deprecated Manim API
- **Mitigation**: Specify "use modern Manim API (not cairo-based)"
- **Fallback**: Post-process code to fix common issues

**Risk**: Duration doesn't match target
- **Mitigation**: Explicitly mention duration in prompt
- **Note**: Exact timing less important than quality

---

## Done When

- [x] Module created with generator function
- [x] System prompt teaches Manim structure
- [x] Can generate code for 3+ different descriptions
- [x] Generated code has correct structure (Scene class, construct)
- [x] Error handling for API failures
- [x] Manual testing with various prompts passes

---

## Follow-up Stories

- **ANIM-002**: Dynamic Code Execution
- **ANIM-003**: Integration with Renderer
- **ANIM-004**: Generation Caching
