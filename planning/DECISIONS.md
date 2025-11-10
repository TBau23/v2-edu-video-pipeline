# Technical Decisions - Locked In ✅

Key architectural decisions for Manim visual rendering.

**Last Updated**: 2025-11-07
**Status**: All 3 critical decisions made and documented

---

## Decision 1: Manim Rendering Approach

**Question**: How do we invoke Manim to render scenes?

**✅ DECISION**: Programmatic API (with CLI fallback)

**Approach**:
```python
from manim import Scene, config

# Configure in Python
config.pixel_width = 1920
config.pixel_height = 1080

# Create and render scene
scene = MyScene()
scene.render()
```

**Why**:
- Cleaner integration (pure Python)
- Better error handling
- Easier debugging
- Can pass data directly

**Fallback**: CLI-based rendering if programmatic doesn't work
- Time-box: 2 hours to validate programmatic approach
- Switch to CLI if needed (implementation ready in executor.py)

**Risks**:
- Manim's programmatic API may be unstable
- Version compatibility issues

**Mitigation**:
- Test early in VIS-001
- CLI fallback is low-risk alternative

**Documented in**: `planning/stories/VIS-001-manim-executor.md`

---

## Decision 2: Scene Composition Strategy

**Question**: Multiple visuals per Act - one scene or multiple scenes?

**✅ DECISION**: One scene per Act

**Approach**:
```python
class ActScene(Scene):
    def construct(self):
        # All visuals in one scene
        title = Text("Title")
        self.play(FadeIn(title))
        self.wait(2)

        equation = MathTex("F = ma")
        self.play(Write(equation))
        self.wait(2)
```

**Result**: One video file per Act with all visuals composed

**Why**:
- Simpler implementation (MVP priority)
- Easier timing control (everything in one place)
- Visuals can interact/reference each other
- Fewer files to manage

**Trade-offs**:
- ❌ Can't cache individual visuals
- ❌ Must re-render whole Act if one visual changes
- ✅ Acceptable for MVP (can optimize later)

**Alternative** (future consideration):
- One scene per visual → composite with ffmpeg
- Better caching, more modular
- More complex, implement if iteration speed becomes bottleneck

**Documented in**: `planning/stories/VIS-008-composition.md`

---

## Decision 3: Timing Control Method

**Question**: How to sync visuals precisely with audio?

**✅ DECISION**: Calculate wait times (MVP) → Absolute timestamps (production)

**MVP Approach** (Approach 1):
```python
# Equation should appear at 6.5s
# Previous visual ended at 2.0s
# Calculate: wait 6.5 - 2.0 = 4.5s

self.wait(4.5)
self.play(Write(equation), run_time=2.0)
```

**Production Approach** (Approach 2):
```python
def render_at_time(self, target_time):
    current = self.renderer.time
    self.wait(max(0, target_time - current))
    self.play(animation)
```

**Timing Workflow**:
1. VisualSpec specifies `trigger_words` (e.g., "mathematically")
2. Match trigger word to audio timestamp (e.g., 6.5s)
3. Visual appears with lead time (e.g., 6.5 - 0.5 = 6.0s)
4. Calculate wait time from previous visual

**Accuracy Targets**:
- MVP: ±500ms (validate pipeline works)
- Production: ±300ms (requirement)
- Stretch: ±100ms (professional quality)

**Why this progression**:
- Approach 1 is simpler, good enough to validate
- Approach 2 more robust for production
- Can upgrade without rewriting

**Expected Precision**:
- Manim: 30fps → ±33ms per frame
- Audio timestamps: ±50ms (estimation) or ±10ms (forced alignment)
- Total: ~±100ms best case

**Should hit ±300ms target with**:
- Word-level timestamps (estimation okay for now)
- Trigger word matching
- Lead time calculation
- Manim's wait() precision

**Documented in**: `planning/stories/VIS-009-timing-control.md`

---

## Impact on Implementation

### VIS-001 (Manim Executor)
- Implement programmatic rendering
- Test with simple scene (circle)
- Have CLI fallback ready
- Time-box: 2 hours

### VIS-008 (Composition)
- Build one scene per Act
- Render all visuals together
- Calculate sequential timing
- Handle simultaneous visuals (VGroup)

### VIS-009 (Timing Control)
- Add trigger_words to VisualSpec
- Match to audio word timestamps
- Calculate visual start times
- Measure accuracy (manual for MVP)

---

## What We're NOT Doing (Yet)

**Not in MVP**:
- ❌ Per-visual caching (whole Act re-renders)
- ❌ Forced alignment (using timestamp estimation)
- ❌ Frame-level timing control
- ❌ Parallel rendering (one Act at a time)

**Can add later if needed**:
- If iteration speed is slow → per-visual caching
- If sync accuracy insufficient → forced alignment
- If ±300ms not achievable → frame-level control

---

## Decision Timeline

All decisions made: **2025-11-07**

**Next steps**:
1. Begin implementation with VIS-001
2. Validate programmatic approach works
3. Build MVP through VIS-005
4. Measure timing accuracy in VIS-009
5. Iterate if targets not met

---

## Change Log

**2025-11-07**: All 3 decisions finalized
- Programmatic API (with CLI fallback)
- One scene per Act
- Calculate wait times → absolute timestamps

**Future**: Will update if implementation reveals need to change approach
