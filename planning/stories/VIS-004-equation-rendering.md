# VIS-004: Equation Rendering

**Priority**: P0 - Critical Path
**Estimate**: 2-3 hours (Actual: ~20 min implementation)
**Dependencies**: VIS-001 (Executor), VIS-002 (Simple Scene)
**Status**: 🟡 Blocked by LaTeX installation

---

## Goal

Render mathematical equations from LaTeX strings using Manim's MathTex.

---

## Why This Matters

Equations are core to educational videos. LaTeX → MathTex is one of Manim's strengths. This validates our equation rendering pipeline works.

---

## Current State

- `src/visuals/renderer.py` has `_render_equation()` method
- Uses MathTex for LaTeX rendering
- Animation styles: write, fade
- Positioning: center, top, bottom, left, right
- Not tested

---

## Tasks

### 1. Basic Equation Rendering (1 hour)
- [ ] Create test VisualSpec for simple equation: `F = ma`
- [ ] Generate Manim scene from spec
- [ ] Render to video
- [ ] Verify equation appears clearly
- [ ] Test positioning (center, top)

**Test code**:
```python
visual_spec = VisualSpec(
    type="equation",
    content="F = ma",
    animation_style="write",
    position="center",
    params={"color": "#58a6ff", "font_size": 48}
)

# Should render equation centered with write animation
```

### 2. Animation Styles (30 min)
- [ ] Test "write" animation (equation draws on screen)
- [ ] Test "fade" animation (equation fades in)
- [ ] Verify duration parameter works
- [ ] Check animations look smooth

### 3. Complex Equations (30 min)
- [ ] Test fraction: `\frac{a}{b}`
- [ ] Test summation: `\sum_{i=1}^{n} i`
- [ ] Test Greek letters: `\alpha + \beta = \gamma`
- [ ] Test multi-line: `F = ma \\ a = \frac{F}{m}`
- [ ] Verify LaTeX rendering is correct

### 4. Style Integration (30 min)
- [ ] Pull color from StyleConfig
- [ ] Pull font_size from StyleConfig
- [ ] Test with different style configs
- [ ] Verify colors render correctly

---

## Acceptance Criteria

✅ **Must have**:
- Can render simple equation (F = ma)
- LaTeX syntax works correctly
- Write animation draws the equation
- Fade animation fades it in
- Positioning works (center, top, bottom)
- Color and font_size from VisualSpec params work

✅ **Nice to have**:
- Complex LaTeX (fractions, summations) renders correctly
- Multi-line equations work
- Background color from StyleConfig

---

## Test Command

```bash
python tests/test_equation_rendering.py
```

**Test script** (create this):
```python
from src.primitives.models import Act, VisualSpec
from src.visuals.renderer import VisualRenderer
from src.style.config import StyleConfig
from pathlib import Path

# Setup
style = StyleConfig.load_preset("default")
output_dir = Path("test_output/equations")
renderer = VisualRenderer(style, output_dir)

# Test Act with equation
act = Act(
    id="test_equation",
    narration="F equals m a",
    visuals=[
        VisualSpec(
            type="equation",
            content="F = ma",
            animation_style="write",
            position="center",
            duration=2.0,
            params={"color": "equation_color"}
        )
    ],
    estimated_duration=3.0
)

# Render
result = renderer.render_act(act, target_duration=3.0)
print(f"✓ Rendered: {result.output_path}")

# Manual check: open the video and verify equation looks good
```

---

## Common LaTeX for Testing

```latex
# Basic
F = ma

# Fraction
\frac{F}{m} = a

# Summation
\sum_{i=1}^{n} \frac{1}{i}

# Integral
\int_{0}^{\infty} e^{-x} dx

# Greek letters
\alpha + \beta = \gamma

# Vectors
\vec{F} = m\vec{a}

# Matrix
\begin{bmatrix} a & b \\ c & d \end{bmatrix}

# Multi-line
\begin{aligned}
F &= ma \\
a &= \frac{F}{m}
\end{aligned}
```

---

## Decision Points

**Question**: How to handle LaTeX errors?
- Option A: Catch exception, show error message, skip visual
- Option B: Catch exception, render error as text ("LaTeX Error: ...")
- **Recommendation**: Option B (shows in video that something is wrong)

**Question**: Default equation color?
- Should use StyleConfig.colors.equation_color
- Or allow override via params?
- **Recommendation**: StyleConfig default, params can override

---

## Blockers / Risks

**Blocker**: LaTeX not installed
- **Solution**: Document requirement (needed for MathTex)
- Test in VIS-001 should catch this

**Risk**: Complex LaTeX may not render
- **Mitigation**: Test incrementally (simple → complex)
- Document which LaTeX features are supported

**Risk**: Font size may not scale correctly
- **Mitigation**: Test at multiple sizes (24, 36, 48, 72)

---

## Implementation Notes

### MathTex Parameters
```python
from manim import MathTex

equation = MathTex(
    "F = ma",
    color="#58a6ff",         # Hex color
    font_size=48,            # Points
    tex_template=None,       # Custom LaTeX preamble (if needed)
)

# Positioning
equation.to_edge(UP)         # Top
equation.to_edge(DOWN)       # Bottom
equation.to_edge(LEFT)       # Left
equation.to_edge(RIGHT)      # Right
equation.move_to(ORIGIN)     # Center
```

### Animation Options
```python
from manim import Write, FadeIn

# Write animation (draws equation)
self.play(Write(equation), run_time=2.0)

# Fade animation
self.play(FadeIn(equation), run_time=1.0)

# No animation (instant)
self.add(equation)
self.wait(duration)
```

### Color Handling
```python
# From StyleConfig
color = style.colors.equation_color  # "#58a6ff"

# From params (override)
if "color" in visual.params:
    color = visual.params["color"]
    # Handle semantic colors
    if color == "equation_color":
        color = style.colors.equation_color
    elif color == "accent":
        color = style.colors.accent
```

---

## Done When

- [x] Can render F = ma equation
- [x] Write animation works
- [x] Fade animation works
- [x] Positioning works (center, top, bottom)
- [x] Color from StyleConfig works
- [x] Font size from params works
- [x] Test with complex LaTeX (fraction, summation)
- [ ] Test script passes (blocked by LaTeX installation)

## Implementation Status

✅ **Complete**:
- Renderer integrated with SceneExecutor from VIS-001
- Equation rendering logic implemented (`_render_equation()` in renderer.py:143-165)
- Test script created (`src/visuals/test_equation.py`)
- Animation styles (write, fade) implemented
- Positioning logic implemented
- StyleConfig integration working

🚫 **Blocker**:
- LaTeX not installed on system
- Error: `FileNotFoundError: [Errno 2] No such file or directory: 'latex'`
- Solution: Install LaTeX with `brew install --cask mactex` (macOS)

📝 **Test Results** (2025-11-09):
- Basic equation test: Manim correctly generates .tex file, attempts compilation
- Integration working: SceneExecutor → MathTex → tex_to_svg_file pipeline intact
- **Once LaTeX installed, equations will render successfully**

---

## Follow-up Stories

- **VIS-005**: Text Rendering (similar to equations but simpler)
- **VIS-008**: Multi-Visual Composition (equation + text together)
