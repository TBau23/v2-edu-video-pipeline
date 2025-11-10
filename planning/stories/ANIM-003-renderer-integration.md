# ANIM-003: Renderer Integration

**Priority**: P0 - Critical Path
**Estimate**: 1 hour
**Dependencies**: ANIM-001, ANIM-002
**Status**: 🔴 Not Started

---

## Goal

Replace AnimationLibrary in the renderer with LLM animation generation, making it work end-to-end in the pipeline.

---

## Why This Matters

This completes the architecture pivot. Once this is done, the full pipeline works with LLM-generated animations instead of predefined ones. Videos can be created for any topic, not just physics.

---

## Current State

- ANIM-001: LLM generates Scene code from descriptions ✓
- ANIM-002: Can execute generated code and render videos ✓
- Renderer still uses AnimationLibrary with predefined animations
- Script generator uses animation names instead of descriptions

---

## Tasks

### 1. Update Renderer (30 min)
- [ ] Import llm_animator functions in `renderer.py`
- [ ] Replace AnimationLibrary call with LLM generation
- [ ] Pass VisualSpec description to generator
- [ ] Execute generated code
- [ ] Handle errors with placeholder fallback
- [ ] Remove AnimationLibrary imports (clean break)

### 2. Update Script Generator (15 min)
- [ ] Revert prompt to use descriptions instead of animation names
- [ ] Remove animation name constraints
- [ ] Encourage detailed, visual descriptions
- [ ] Test with various topics

### 3. Update Tests (15 min)
- [ ] Update test_animation_integration.py
- [ ] Change from animation names to descriptions
- [ ] Test with various subjects (not just physics)
- [ ] Verify E2E pipeline works

---

## Implementation

### Renderer Changes

**Before** (`src/visuals/renderer.py`):
```python
def _render_animation(self, visual: VisualSpec, duration: float):
    anim_name = visual.content
    try:
        anim_func = AnimationLibrary.get_animation(anim_name)
        mobject, animations, actual_duration = anim_func(**params)
        # ... render ...
    except KeyError:
        # Placeholder
```

**After**:
```python
from src.visuals.llm_animator import generate_animation_scene, execute_animation_code

def _render_animation(self, visual: VisualSpec, duration: float):
    """Render animation using LLM generation."""

    description = visual.content
    logger.info(f"Generating animation: {description[:50]}...")

    try:
        # Generate Scene code from description
        code = generate_animation_scene(
            description=description,
            duration=duration,
            api_key=self.openai_key  # Need to pass through
        )

        # Execute code and render
        output_path = execute_animation_code(
            code=code,
            output_name=f"anim_{hash(description)}",
            output_dir=self.output_dir / "animations",
            quality=self.quality
        )

        # Output path is already a video file
        # Copy to expected location
        return output_path

    except Exception as e:
        # Fallback to placeholder
        logger.error(f"Animation generation failed: {e}")
        self._render_placeholder(visual, duration)
```

### Constructor Update

Need to pass OpenAI key to renderer:
```python
class VisualRenderer:
    def __init__(
        self,
        style: StyleConfig,
        output_dir: Path,
        quality: str = "medium_quality",
        openai_key: Optional[str] = None  # NEW
    ):
        self.openai_key = openai_key
        # ...
```

Update orchestrator to pass key:
```python
renderer = VisualRenderer(
    style=style,
    output_dir=visuals_dir,
    quality="medium_quality",
    openai_key=openai_key  # NEW
)
```

### Script Generator Changes

**Before** (current system prompt):
```
### 3. animation
For dynamic Manim scenes. Use animation names from the AnimationLibrary.

**Available animations:**
- **car_accelerating**: Car accelerating from rest
- **hockey_puck_sliding**: Puck sliding at constant velocity
...

**Usage:** Set `content` to the exact animation name:
{
  "type": "animation",
  "content": "car_accelerating",
  ...
}
```

**After** (revert to descriptions):
```
### 3. animation
For dynamic Manim scenes. Describe what should be animated clearly and visually.

**Guidelines:**
- Be specific about objects, motion, and visual details
- Describe colors, shapes, and positioning
- Mention key visual elements (arrows, labels, motion lines)
- Focus on what viewers should SEE

**Examples:**
{
  "type": "animation",
  "content": "A blue car (rectangle with circular wheels) accelerating from left to right, with motion lines trailing behind showing increasing speed",
  "duration": 4.0,
  ...
}

{
  "type": "animation",
  "content": "A hockey puck (gray disk) sliding across ice at constant velocity, with faint motion lines and a light blue ice surface below",
  "duration": 3.0,
  ...
}
```

---

## Acceptance Criteria

✅ **Must have**:
- Full E2E pipeline works with LLM animations
- Can generate video for physics topics (existing)
- Can generate video for non-physics topics (new capability)
- Fallback to placeholder works on errors
- No references to AnimationLibrary in code

✅ **Nice to have**:
- Animation quality is "good enough"
- Duration roughly matches target
- Works for variety of subjects

---

## Test Strategy

### Integration Test

```python
def test_e2e_with_llm_animations():
    """Test full pipeline with LLM-generated animations."""

    # Create Act with descriptive animation
    visual = VisualSpec(
        type="animation",
        content="A red blood cell flowing through a blood vessel, showing its flexible disk shape as it squeezes through narrow capillaries",
        duration=4.0,
        position="center",
        params={}
    )

    act = Act(
        id="test_biology",
        narration="Red blood cells transport oxygen throughout your body",
        visuals=[visual],
        estimated_duration=4.0
    )

    # Render
    style = StyleConfig.load_preset("default")
    renderer = VisualRenderer(
        style=style,
        output_dir=Path("test_output/llm_animations"),
        quality="low_quality",
        openai_key=os.getenv("OPENAI_API_KEY")
    )

    result = renderer.render_act(act, target_duration=4.0)

    # Verify
    assert result.output_path.exists()
    assert result.duration == 4.0
```

### E2E Test

Run full pipeline with various topics:
```bash
# Physics (should still work)
python examples/generate_video.py --prompt "Explain Newton's First Law"

# Biology (new capability!)
python examples/generate_video.py --prompt "Explain how photosynthesis works"

# Chemistry (new capability!)
python examples/generate_video.py --prompt "Explain ionic bonding"
```

---

## Rollout Strategy

### Option A: Clean Break
- Remove AnimationLibrary completely
- All animations use LLM generation
- **Pro**: Simpler codebase
- **Con**: No fallback to known-good animations

### Option B: Hybrid Approach
- Try AnimationLibrary first
- Fall back to LLM if not found
- **Pro**: Safer, keeps working examples
- **Con**: More complexity, maintenance burden

**Recommendation**: Option A - trust LLM generation, clean architecture

---

## Error Handling

### Graceful Degradation

```python
def _render_animation(self, visual: VisualSpec, duration: float):
    try:
        # Try LLM generation
        output_path = self._generate_llm_animation(visual, duration)
        return output_path

    except Exception as e:
        logger.error(f"LLM animation failed: {e}")

        # Fallback to simple placeholder
        return self._render_placeholder(visual, duration)


def _render_placeholder(self, visual: VisualSpec, duration: float):
    """Show text placeholder when animation fails."""
    placeholder = Text(
        f"[Animation: {visual.content[:50]}...]",
        font_size=24,
        color=style.colors.secondary
    )
    placeholder = self._apply_position(placeholder, visual.position)

    self.play(FadeIn(placeholder), run_time=duration * 0.2)
    self.wait(duration * 0.6)
    self.play(FadeOut(placeholder), run_time=duration * 0.2)
```

---

## Monitoring

### Metrics to Track
- **Success rate**: % of animations that render successfully
- **Generation time**: How long LLM call takes
- **Render time**: How long execution takes
- **Error types**: What failures occur most often

### Logging
```python
logger.info(f"Generating animation: {description[:50]}")
logger.info(f"Generation took {gen_time:.1f}s")
logger.info(f"Render took {render_time:.1f}s")

if error:
    logger.error(f"Animation failed: {type(error).__name__}: {error}")
    logger.debug(f"Generated code:\n{code}")
```

---

## Blockers / Risks

**Risk**: Generation is too slow for pipeline
- **Current**: Each animation takes ~3-5s to generate + render
- **Pipeline**: 5 acts × 2 animations = 10 animations = ~50s
- **Mitigation**: Cache successful generations (ANIM-004)
- **Acceptable**: 50s is reasonable for video generation

**Risk**: Quality is inconsistent
- **Mitigation**: Prompt engineering (ANIM-007)
- **Fallback**: Placeholder shows at least content exists
- **Future**: Human review/refinement workflow

**Risk**: Cost too high
- **Per video**: ~$0.10-0.15 in LLM calls
- **Acceptable**: Comparable to TTS costs
- **Mitigation**: Aggressive caching

---

## Done When

- [x] Renderer uses LLM generation instead of AnimationLibrary
- [x] Script generator creates descriptive content
- [x] Full E2E pipeline works with LLM animations
- [x] Can generate videos for non-physics topics
- [x] Fallback to placeholder works
- [x] AnimationLibrary code removed
- [x] Tests updated and passing

---

## Follow-up Stories

- **ANIM-004**: Generation Caching (reduce costs)
- **ANIM-005**: Script Generator Optimization
- **ANIM-006**: Error Recovery
- **ANIM-007**: Prompt Engineering
