# VIS-007: Animation Library Integration

**Priority**: P1 - High Priority
**Estimate**: 6-8 hours (Actual: ~2 hours)
**Dependencies**: VIS-001, VIS-002, VIS-004
**Status**: 🟢 Complete

---

## Goal

Connect VisualSpec animations to the AnimationLibrary and get physics animations rendering.

---

## Why This Matters

This is where educational value comes from. Static equations are fine, but animations that show **motion, forces, and concepts** are what make videos effective teaching tools.

---

## Current State

- `src/visuals/animations.py` has animation functions defined
- `AnimationLibrary` registry exists
- `_render_animation()` in renderer.py shows placeholder text
- **No actual integration** between VisualSpec → animation function → Manim

---

## Problem Statement

**Gap**: VisualSpec has animation name + params, but we don't know:
1. How to look up the animation function
2. How to pass VisualSpec params to animation function
3. How to integrate animation mobjects into the scene
4. How to control timing/duration

**Example VisualSpec**:
```json
{
  "type": "animation",
  "content": "car_accelerating",
  "animation_style": "play",
  "duration": 4.0,
  "params": {
    "start_pos": [-4, 0, 0],
    "end_pos": [4, 0, 0],
    "acceleration": 1.5,
    "show_motion_lines": true
  }
}
```

**Need to**:
1. Look up `car_accelerating` in AnimationLibrary
2. Call function with params
3. Get mobjects + animations + duration back
4. Add to scene with proper timing

---

## Tasks

### 1. Design Parameter Mapping (2 hours)

**Challenge**: VisualSpec params are JSON. Animation functions expect Python types.

**Need to handle**:
- Lists → tuples (e.g., `[4, 0, 0]` → `(4, 0, 0)` for positions)
- Strings → Manim constants (e.g., `"UP"` → `UP`, `"BLUE"` → `BLUE`)
- Booleans, numbers (already work)

**Tasks**:
- [ ] Create param conversion function
- [ ] Handle Manim constant lookups (UP, DOWN, LEFT, RIGHT, colors)
- [ ] Document param types for each animation

**Example**:
```python
def convert_params(params: dict) -> dict:
    """Convert VisualSpec params to animation function kwargs."""
    converted = {}
    for key, value in params.items():
        if isinstance(value, list) and key.endswith("_pos"):
            # Convert position lists to numpy arrays
            converted[key] = np.array(value)
        elif isinstance(value, str) and value in MANIM_CONSTANTS:
            # Convert string to Manim constant
            converted[key] = MANIM_CONSTANTS[value]
        else:
            converted[key] = value
    return converted
```

### 2. Fix Animation Function Signatures (2 hours)

**Problem**: Current animation functions return `(mobjects, animations, duration)` tuples. Need consistent API.

**Tasks**:
- [ ] Review all animation functions in animations.py
- [ ] Standardize return type
- [ ] Ensure duration parameter works
- [ ] Test each animation independently

**Example**:
```python
@staticmethod
def car_accelerating(
    start_pos=LEFT * 4,
    end_pos=RIGHT * 4,
    acceleration=1.0,
    duration=3.0,
    show_motion_lines=True,
    **kwargs
):
    """
    Returns:
        tuple: (mobject, list_of_animations, actual_duration)
    """
    # Create car
    car = VGroup(...)

    # Create animation
    anim = car.animate(rate_func=...).move_to(end_pos)

    return car, [anim], duration
```

### 3. Integrate into Renderer (2 hours)

**Update `_render_animation()` in renderer.py**:

```python
def _render_animation(self, visual: VisualSpec, duration: float):
    """Render a custom animation from the library."""

    # Look up animation in library
    anim_name = visual.content
    try:
        anim_func = AnimationLibrary.get_animation(anim_name)
    except KeyError:
        # Animation not found, show placeholder
        placeholder = Text(f"[Animation not found: {anim_name}]")
        self.play(FadeIn(placeholder), run_time=1.0)
        return

    # Convert params
    params = convert_params(visual.params)
    params['duration'] = duration

    # Call animation function
    mobject, animations, actual_duration = anim_func(**params)

    # Position mobject if needed
    mobject = self._apply_position(mobject, visual.position)

    # Add to scene
    self.add(mobject)

    # Play animations
    for anim in animations:
        if hasattr(anim, '__iter__'):
            # Multiple simultaneous animations
            self.play(*anim)
        else:
            self.play(anim)
```

### 4. Test Individual Animations (2 hours)

Test each animation in isolation:

- [ ] car_accelerating
- [ ] hockey_puck_sliding
- [ ] object_at_rest
- [ ] person_in_braking_car

**Test script**:
```python
# Test car animation
visual = VisualSpec(
    type="animation",
    content="car_accelerating",
    animation_style="play",
    duration=4.0,
    params={
        "acceleration": 1.5,
        "show_motion_lines": True
    }
)

act = Act(
    id="test_car",
    narration="A car accelerates",
    visuals=[visual],
    estimated_duration=4.0
)

renderer.render_act(act)
# Should show car accelerating from left to right
```

---

## Acceptance Criteria

✅ **Must have**:
- Can render `car_accelerating` animation from VisualSpec
- Parameters from VisualSpec params are passed correctly
- Animation plays smoothly
- Duration matches specified duration
- At least 2 animations working (car, hockey puck)

✅ **Nice to have**:
- All 4 physics animations working
- Parameter validation (helpful error messages)
- Animation preview (low-res fast render)

---

## Test Command

```bash
python tests/test_animation_integration.py
```

**Expected output**:
```
Testing car_accelerating...
  ✓ Animation rendered
  ✓ Parameters applied correctly
  ✓ Duration: 4.0s

Testing hockey_puck_sliding...
  ✓ Animation rendered
  ✓ Duration: 3.0s

All animations working!
```

---

## Decision Points

**Question**: How to handle animation not found?
- Option A: Raise error (fail fast)
- Option B: Show placeholder text in video
- Option C: Log warning, skip visual
- **Recommendation**: Option B (user sees what's missing)

**Question**: How to handle parameter type mismatches?
- Option A: Strict validation, fail if wrong type
- Option B: Try to convert, fallback to default if fails
- **Recommendation**: Option B (more forgiving)

**Question**: Should animations be composable (multiple animations in one visual)?
- Currently: One animation per VisualSpec
- Future: Could support multiple simultaneous animations
- **Decision**: Keep simple for now, revisit if needed

---

## Blockers / Risks

**Blocker**: Animation functions may have bugs
- **Mitigation**: Test each individually before integration
- Fix bugs in animations.py as discovered

**Risk**: Parameter conversion complex
- **Mitigation**: Start with simple types (numbers, booleans)
- Add complex types (positions, colors) incrementally

**Risk**: Manim constant lookup fragile
- **Mitigation**: Whitelist known constants
- Document which constants are supported

---

## Implementation Notes

### Manim Constants to Support

```python
MANIM_CONSTANTS = {
    # Directions
    "UP": UP,
    "DOWN": DOWN,
    "LEFT": LEFT,
    "RIGHT": RIGHT,

    # Colors
    "BLUE": BLUE,
    "RED": RED,
    "GREEN": GREEN,
    "YELLOW": YELLOW,
    "GRAY": GRAY,

    # Add more as needed
}
```

### Parameter Patterns

Common param types:
- **Position**: `[x, y, z]` → `np.array([x, y, z])`
- **Color**: `"BLUE"` or `"#0000ff"` → `BLUE` or hex string
- **Duration**: `3.0` → `3.0` (float)
- **Boolean flags**: `true` → `True`

### Animation Function Contract

All animation functions should follow this pattern:

```python
def my_animation(
    # Required params with defaults
    duration=2.0,
    **kwargs  # Accept extra params gracefully
):
    """
    Create an animation.

    Args:
        duration: Animation duration in seconds
        **kwargs: Additional parameters

    Returns:
        tuple: (mobject, list_of_animations, actual_duration)
    """
    mobject = create_mobject()
    animations = [mobject.animate.something()]
    return mobject, animations, duration
```

---

## Done When

- [x] Can look up animations from AnimationLibrary
- [x] Parameters convert from JSON → Python correctly
- [x] car_accelerating animation renders
- [x] hockey_puck_sliding animation renders
- [x] Duration control works
- [x] Positioning works (apply_position)
- [x] Test script passes with at least 2 animations

---

## Follow-up Stories

- **VIS-007b**: Add more physics animations (projectile, pendulum, etc.)
- **VIS-008**: Multi-Visual Composition (animation + equation + text)
- **VIS-009**: Timing Control (sync with audio timestamps)
