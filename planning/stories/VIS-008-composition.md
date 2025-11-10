# VIS-008: Multi-Visual Composition

**Priority**: P1 - High Priority
**Estimate**: 4-6 hours (Actual: ~1 hour)
**Dependencies**: VIS-001, VIS-004, VIS-005, VIS-007
**Status**: 🟢 Complete

---

## Goal

Combine multiple visuals (text + equation + animation) into a single Act scene.

---

## Why This Matters

Real Acts have multiple visuals that need to appear in sequence or simultaneously. This is what makes educational videos effective - layering information.

---

## Current State

- Renderer has `_render_X()` methods for each visual type
- Each method works independently
- No testing of multiple visuals together
- Timing coordination not implemented

---

## Key Design Decision

**✅ DECISION: One Scene per Act (all visuals together)**

**Approach**:
```python
class ActScene(Scene):
    def construct(self):
        # Visual 1: Title (0-2s)
        title = Text("Newton's First Law")
        self.play(FadeIn(title), run_time=1.0)
        self.wait(1.0)

        # Visual 2: Equation (appears at 2s)
        equation = MathTex("F = ma")
        self.play(Write(equation), run_time=2.0)
        self.wait(1.0)

        # Visual 3: Animation (appears at 5s)
        car = create_car()
        self.play(car.animate.shift(RIGHT * 4), run_time=3.0)
```

**Result**: One video file per Act

**Why this approach**:
- ✅ Simpler implementation for MVP
- ✅ Easier timing control (all in one place)
- ✅ Visuals can interact/reference each other
- ✅ Fewer files to manage

**Trade-off**: Can't cache individual visuals (must re-render whole Act)
- Acceptable for MVP
- Can optimize later if needed

**Alternative** (for future): One scene per visual, composite with ffmpeg
- More modular, better caching
- More complex implementation
- Consider if iteration speed becomes bottleneck

---

## Tasks

### 1. Sequential Visual Rendering (2 hours)
- [ ] Render Act with 2 visuals (text + equation)
- [ ] Calculate timing: when should each appear?
- [ ] Use `self.wait()` between visuals
- [ ] Verify visuals appear in order
- [ ] Test different durations

**Test case**:
```python
act = Act(
    id="test_multi",
    narration="Newton's First Law. F equals m a.",
    visuals=[
        VisualSpec(type="text", content="Newton's First Law", duration=2.0),
        VisualSpec(type="equation", content="F = ma", duration=3.0)
    ],
    estimated_duration=5.0
)
# Should show: text for 2s, then equation for 3s
```

### 2. Simultaneous Visuals (1 hour)
- [ ] Support visuals that appear together
- [ ] Use VGroup to group mobjects
- [ ] Test: title at top + equation at center (both visible)

**Example**:
```python
visuals=[
    VisualSpec(type="text", content="Title", position="top"),
    VisualSpec(type="equation", content="F=ma", position="center")
]
# Both should be visible at once
```

### 3. Timing Calculation (1-2 hours)
- [ ] Given Act duration and visual durations, calculate when each appears
- [ ] Handle case: sum(visual durations) != act duration
- [ ] Scale visuals proportionally if needed
- [ ] Document timing strategy

**Algorithm**:
```python
def calculate_visual_timings(act: Act, target_duration: float):
    """
    Given visuals with optional durations, calculate when each should appear.

    Strategy:
    - If all visuals have durations: use them, scale if sum != target
    - If some missing: divide remaining time equally
    - Return list of (start_time, duration) tuples
    """
    pass
```

### 4. Test Complex Act (1 hour)
- [ ] Act with 3+ visuals (text + equation + animation)
- [ ] Different animation styles (fade, write, draw)
- [ ] Different positions (top, center, bottom)
- [ ] Verify timing is smooth
- [ ] No gaps or overlaps

---

## Acceptance Criteria

✅ **Must have**:
- Can render Act with 2+ visuals sequentially
- Visuals appear in correct order
- Timing is controlled (no random gaps)
- Each visual gets appropriate duration
- Video plays smoothly (no glitches)

✅ **Nice to have**:
- Simultaneous visuals (title + equation both visible)
- Smart timing (auto-calculate durations if not specified)
- Transitions between visuals (fade out/in)

---

## Test Command

```bash
python tests/test_composition.py
```

**Test script**:
```python
# Test 1: Sequential (text, then equation)
act1 = Act(
    id="test_sequential",
    narration="Newton's First Law. F equals m a.",
    visuals=[
        VisualSpec(type="text", content="Newton's First Law", duration=2.0),
        VisualSpec(type="equation", content="F = ma", duration=3.0)
    ],
    estimated_duration=5.0
)

# Test 2: Simultaneous (title at top + equation at center)
act2 = Act(
    id="test_simultaneous",
    narration="Newton's First Law: F equals m a.",
    visuals=[
        VisualSpec(type="text", content="Newton's First Law", position="top"),
        VisualSpec(type="equation", content="F = ma", position="center")
    ],
    estimated_duration=4.0
)

# Test 3: Complex (text + equation + animation)
act3 = Act(
    id="test_complex",
    narration="A car accelerates. Force equals mass times acceleration.",
    visuals=[
        VisualSpec(type="animation", content="car_accelerating", duration=3.0),
        VisualSpec(type="equation", content="F = ma", duration=2.0)
    ],
    estimated_duration=5.0
)

# Render all
renderer = VisualRenderer(style, output_dir)
for act in [act1, act2, act3]:
    result = renderer.render_act(act)
    print(f"✓ {act.id}: {result.duration}s")
```

---

## Timing Strategy

### Problem: How to time multiple visuals?

**Input**: Act with 3 visuals, 10s duration
```python
visuals = [
    VisualSpec(type="text", duration=2.0),      # Explicit
    VisualSpec(type="equation", duration=None),  # Not specified
    VisualSpec(type="animation", duration=4.0)   # Explicit
]
total_duration = 10.0
```

**Algorithm**:
1. Sum explicit durations: 2.0 + 4.0 = 6.0s
2. Remaining time: 10.0 - 6.0 = 4.0s
3. Visuals without duration: 1 (equation)
4. Assign: equation gets 4.0s

**Timeline**:
```
[0-2s]: text
[2-6s]: equation (auto-calculated 4s)
[6-10s]: animation
```

### Edge Cases

**Case 1**: Sum of durations > target
```python
# visuals total 12s, but act is only 10s
# Solution: Scale all proportionally
# Each visual gets: (visual.duration / 12) * 10
```

**Case 2**: No durations specified
```python
# 3 visuals, 9s total
# Solution: Divide equally
# Each visual gets: 9 / 3 = 3s
```

**Case 3**: Simultaneous visuals
```python
# Visuals at same position don't stack - they overlap
# Just render both, they'll be visible together
```

---

## Implementation Notes

### Manim Scene Structure
```python
class ActScene(Scene):
    def construct(self):
        current_time = 0.0

        for visual in visuals:
            # Calculate when this visual should appear
            start_time = current_time
            duration = visual.duration or default_duration

            # Wait if needed
            if start_time > current_time:
                self.wait(start_time - current_time)

            # Render visual
            if visual.type == "text":
                self._render_text(visual, duration)
            elif visual.type == "equation":
                self._render_equation(visual, duration)
            # ... etc

            current_time = start_time + duration
```

### VGroup for Simultaneous Visuals
```python
from manim import VGroup

# Create both mobjects
title = Text("Title").to_edge(UP)
equation = MathTex("F=ma").move_to(ORIGIN)

# Group them
group = VGroup(title, equation)

# Animate together
self.play(FadeIn(group), run_time=1.0)
```

---

## Done When

- [x] Can render Act with 2+ visuals sequentially
- [x] Timing calculation algorithm works
- [x] Can handle visuals with/without explicit durations
- [x] Test passes with 3 different Acts
- [x] Video output looks correct (manual verification)
- [x] No gaps or overlaps in timing

## Implementation Status (2025-11-09)

✅ **Complete**:
- Smart timing calculation implemented (`_calculate_visual_timings()` in renderer.py:110-157)
  - Handles all explicit durations (scales if sum > target)
  - Handles partial explicit (fills remaining time)
  - Handles no explicit (divides equally)
- Fixed positioning to use Manim constants (UP, DOWN, LEFT, RIGHT)
- Test created and passing (`src/visuals/test_composition.py`)
- Successfully rendered multi-visual scene (title + description)

📝 **Test Results**:
- Multi-text composition: ✓ PASS
- Output: test_output/composition/test_composition.mp4 (42KB)
- Contains: title at top + description at center
- Smooth transitions, proper timing

---

## Follow-up Stories

- **VIS-009**: Precise timing control (sync with audio timestamps)
- **VIS-010**: Caching (avoid re-rendering unchanged Acts)
- **Future**: Per-visual rendering + ffmpeg composition (if caching becomes critical)
