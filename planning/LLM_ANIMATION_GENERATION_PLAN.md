# LLM Animation Generation - Architecture Pivot

Switching from predefined animation library to LLM-generated Manim code.

## Overview

**Current approach**: AnimationLibrary with ~6 predefined animations (car_accelerating, hockey_puck_sliding, etc.)

**Problem**:
- Limited to physics topics
- Manual work to add each animation
- Won't scale to biology, chemistry, history, etc.
- Generic shapes don't fit specific educational moments

**New approach**: LLM generates Manim Scene code on-demand from VisualSpec descriptions

**Benefits**:
- ✅ Unlimited flexibility - works for any subject
- ✅ Custom visualizations per concept
- ✅ No manual coding of animations
- ✅ Script generator already creates good descriptions
- ✅ Cost reasonable (~$0.01-0.05 per animation)

**Risks**:
- ❌ Generated code might be buggy
- ❌ Slower (extra LLM call per animation)
- ❌ Need good error handling

---

## Architecture Change

### Before (VIS-007 Implementation)
```
VisualSpec(content="hockey_puck_sliding")
  → AnimationLibrary.get_animation("hockey_puck_sliding")
  → Predefined function returns (mobject, animations, duration)
  → Renderer plays animations
```

### After (LLM Generation)
```
VisualSpec(content="A hockey puck sliding across ice at constant velocity")
  → LLM generates Manim Scene code
  → Execute code dynamically to create Scene class
  → Render Scene using SceneExecutor
  → Output video file
```

---

## What Changes

1. **Script Generator** - Revert to descriptive content instead of animation names
   - Change: "hockey_puck_sliding" → "A hockey puck sliding across ice..."
   - Already worked this way before VIS-007

2. **Animation Code Generator** (NEW) - `src/visuals/llm_animator.py`
   - Takes VisualSpec description + duration
   - Constructs prompt with Manim best practices
   - Calls GPT-4 to generate Scene code
   - Returns executable Python code

3. **Renderer** - Update `_render_animation()` method
   - Call LLM generator instead of AnimationLibrary
   - Execute generated code safely
   - Fallback to placeholder on error

4. **Caching** (optional) - Cache successful generations
   - Hash description → generated code
   - Reuse known-good animations
   - Build library over time automatically

---

## What Stays The Same

- ✅ All rendering infrastructure (SceneExecutor, timing, composition)
- ✅ Script → Audio → Visuals → Assembly pipeline
- ✅ Equation, text, graph rendering (unchanged)
- ✅ Video assembly and stitching
- ✅ Full E2E orchestration

**Only change**: How animation visuals are created

---

## Stories

### Phase 1: Core LLM Generation (Priority: P0)

**ANIM-001: LLM Animation Code Generator** (2 hours)
- Create `src/visuals/llm_animator.py`
- Implement `generate_animation_scene()` function
- Construct prompt with Manim best practices
- Return executable Scene code
- Test with simple animation

**ANIM-002: Dynamic Code Execution** (1 hour)
- Safely execute generated Scene code
- Create Scene class from code string
- Handle imports and Manim setup
- Error handling and validation
- Test with various generated codes

**ANIM-003: Integration with Renderer** (1 hour)
- Update `_render_animation()` to call LLM generator
- Execute generated Scene using SceneExecutor
- Fallback to placeholder on failure
- Logging for debugging
- Test end-to-end rendering

### Phase 2: Optimization (Priority: P1)

**ANIM-004: Generation Caching** (1 hour)
- Hash-based cache for generated code
- Store successful generations
- Reuse cached code on same description
- Cache invalidation strategy

**ANIM-005: Script Generator Update** (30 min)
- Revert to descriptive animation content
- Update system prompt
- Remove animation name constraints
- Test with various topics

### Phase 3: Quality & Reliability (Priority: P2)

**ANIM-006: Error Recovery** (1 hour)
- Retry logic for failed generations
- Better error messages
- Validation of generated code structure
- Metrics/logging for failures

**ANIM-007: Prompt Engineering** (ongoing)
- Improve generation prompt based on failures
- Add examples of good Manim code
- Constraints for video-safe animations
- Duration control improvements

---

## Dependencies Graph

```
ANIM-001 (LLM Generator) ──→ ANIM-002 (Code Execution) ──→ ANIM-003 (Integration)
                                                                ↓
                                                    [Full E2E Pipeline Works]
                                                                ↓
                                                    ANIM-004 (Caching)
                                                    ANIM-005 (Script Update)
                                                                ↓
                                                    ANIM-006 (Error Recovery)
                                                    ANIM-007 (Prompt Engineering)
```

**Critical path**: ANIM-001 → ANIM-002 → ANIM-003

**Estimated total**: ~4-5 hours for Phase 1 (MVP)

---

## Implementation Strategy

### Step 1: Build Generator (ANIM-001)
Create prompt that generates clean Manim Scene code:
```python
def generate_animation_scene(description: str, duration: float) -> str:
    """Generate Manim Scene code from description.

    Args:
        description: What to animate (e.g., "A car accelerating from rest")
        duration: Target duration in seconds

    Returns:
        Python code defining a Scene class
    """
    # Construct prompt with Manim best practices
    # Call GPT-4
    # Return Scene code
```

### Step 2: Execute Code Safely (ANIM-002)
```python
def execute_animation_code(code: str, output_path: Path) -> Path:
    """Execute generated Scene code and render.

    Args:
        code: Python code with Scene class definition
        output_path: Where to save rendered video

    Returns:
        Path to rendered video file
    """
    # Parse code to extract Scene class
    # Execute with proper imports
    # Use SceneExecutor to render
    # Handle errors gracefully
```

### Step 3: Integrate (ANIM-003)
Update `renderer.py`:
```python
def _render_animation(self, visual: VisualSpec, duration: float):
    """Render animation using LLM generation."""

    # Generate Scene code from description
    code = generate_animation_scene(visual.content, duration)

    try:
        # Execute and render
        output_path = execute_animation_code(code, self.output_dir)
        return output_path
    except Exception as e:
        # Fallback to placeholder
        logger.error(f"Animation generation failed: {e}")
        self._render_placeholder(visual, duration)
```

---

## Testing Strategy

### Unit Tests
- `test_llm_animator.py`: Test code generation
- `test_code_execution.py`: Test safe execution
- Mock OpenAI responses for fast tests

### Integration Tests
- Generate + render simple animations
- Test various description types
- Verify error handling

### E2E Tests
- Full pipeline with LLM-generated animations
- Test on multiple subjects (physics, biology, etc.)
- Compare quality to predefined animations

---

## Rollout Plan

### Option A: Complete Replacement
- Remove AnimationLibrary entirely
- All animations use LLM generation
- Faster to implement
- Higher risk if generation fails

### Option B: Hybrid Approach (RECOMMENDED)
- Try AnimationLibrary first (for backward compatibility)
- Fall back to LLM generation if animation not found
- Keeps working examples as reference
- Safer migration path

**Recommendation**: Option A - Clean break, simpler codebase, trust LLM quality

---

## Success Criteria

✅ **Must have** (Phase 1):
- LLM generates valid Manim Scene code
- Code executes without errors (90%+ success rate)
- Rendered animations appear in video
- Duration roughly matches target
- Fallback to placeholder works

✅ **Nice to have** (Phase 2+):
- Caching reduces LLM calls by 50%+
- Works for non-physics topics
- Generation time < 3 seconds
- Quality subjectively "good enough"

---

## Cost Analysis

**Before**: $0 per animation (predefined)

**After**:
- LLM call: ~$0.01-0.05 per animation
- Typical video (5 acts, 2 animations): $0.10
- With caching (50% hit rate): $0.05/video

**Comparison to other costs**:
- TTS: ~$0.05-0.15 per video
- Script generation: ~$0.01-0.03 per video
- **Total video cost**: ~$0.15-0.30 → LLM animations add ~30%

**Verdict**: Cost increase is acceptable for unlimited flexibility

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Generated code is buggy | High | Medium | Try/catch, fallback, retry logic |
| LLM hallucinates invalid Manim API | Medium | Low | Constrain prompt, validate code structure |
| Generation is too slow | Medium | Low | Caching, async generation |
| Quality is poor | High | Medium | Prompt engineering, examples in prompt |
| Cost spirals | Low | Low | Cache aggressively, monitor usage |

---

## Open Questions

1. **Should we keep AnimationLibrary as fallback?**
   - Pro: Safety net for known animations
   - Con: More complexity, maintenance burden
   - **Decision**: Remove it, trust LLM generation

2. **How to validate generated code before execution?**
   - Check for Scene class definition
   - Validate imports
   - AST parsing for dangerous operations?
   - **Decision**: Start simple, add validation if needed

3. **What duration tolerance is acceptable?**
   - Target: ±10% of requested duration
   - If too short: add wait() calls
   - If too long: warn but allow
   - **Decision**: Be lenient, prioritize quality over exact timing

4. **Should animations be cached globally or per-project?**
   - Global: More cache hits, but less control
   - Per-project: More isolated, but more regeneration
   - **Decision**: Global cache with hash-based keys

---

## Next Steps

1. ✅ Create this planning doc
2. → Create story files (ANIM-001, ANIM-002, ANIM-003)
3. → Implement ANIM-001 (LLM generator)
4. → Implement ANIM-002 (code execution)
5. → Implement ANIM-003 (integration)
6. → Test E2E with various topics
7. → Iterate on prompt engineering

**Estimated time to working MVP**: 4-5 hours
