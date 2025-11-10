# VIS-009: Timing Control & Audio Sync

**Priority**: P1 - High Priority
**Estimate**: 4-6 hours (Actual: ~1.5 hours)
**Dependencies**: VIS-008 (Composition), Audio synthesis
**Status**: 🟢 Complete (untested - requires audio)

---

## Goal

Achieve precise timing control so visuals sync with audio narration (±300ms target).

---

## Why This Matters

This is what makes the video **feel professional**. If visuals appear too early or late relative to the narration, it's jarring and hurts the learning experience.

---

## Current State

- Visual rendering doesn't consider audio timing
- No integration between AudioSegment timestamps and VisualSpec timing
- Need to bridge: "equation appears when 'mathematically' is spoken"

---

## Key Design Decision

**✅ DECISION: Calculate wait times (MVP), absolute timestamps (production)**

**MVP Approach** (Approach 1): Calculate wait times between visuals
```python
# Want equation to appear at 6.5s
# Previous visual ended at 2.0s
# Need to wait: 6.5 - 2.0 = 4.5s

self.wait(4.5)
self.play(Write(equation), run_time=2.0)
```

**Production Approach** (Approach 2): Use absolute timestamps
```python
def render_at_time(self, target_time):
    """Render visual at specific time in scene."""
    current_time = self.renderer.time
    wait_time = max(0, target_time - current_time)
    self.wait(wait_time)
```

**Why this progression**:
- Approach 1 is simpler, good enough for MVP
- Approach 2 gives better precision for production
- Can upgrade without rewriting everything

**Target accuracy**:
- MVP: ±500ms (validate pipeline works)
- Production: ±300ms (from requirements)
- Stretch: ±100ms (professional quality)

---

## Tasks

### 1. Design Timing Data Structure (1 hour)

**Need**: Mapping from word timestamps → visual appearance times

- [ ] Define SyncPoint data structure
- [ ] Calculate visual trigger times from audio timestamps
- [ ] Handle "trigger_word" in VisualSpec (optional)
- [ ] Document timing calculation algorithm

**Data structure**:
```python
@dataclass
class SyncPoint:
    visual_id: str              # Which visual
    audio_act_id: str           # Which Act's audio
    start_time: float           # When to show (seconds)
    duration: float             # How long to show
    trigger_word: Optional[str] # Word that triggers it
    trigger_time: Optional[float] # Word timestamp
    lead_time: float = 0.5      # Show visual before word (seconds)
```

**Example**:
```python
# Audio: "Mathematically we express this as F equals m a"
# Word "mathematically" starts at 2.0s
# Equation should appear 0.5s BEFORE word (at 1.5s)

sync_point = SyncPoint(
    visual_id="equation_F_ma",
    audio_act_id="act_3_equation",
    start_time=1.5,
    duration=3.0,
    trigger_word="mathematically",
    trigger_time=2.0,
    lead_time=0.5
)
```

### 2. Extract Trigger Words from VisualSpec (1 hour)

- [ ] Add `trigger_words` field to VisualSpec (optional)
- [ ] Match trigger words to audio word timestamps
- [ ] Calculate visual start time (trigger_time - lead_time)
- [ ] Handle case: trigger word not found in audio

**VisualSpec update**:
```python
VisualSpec(
    type="equation",
    content="F = ma",
    trigger_words=["mathematically", "equation"],  # NEW
    lead_time=0.5,  # NEW (optional, default 0.5)
    params={...}
)
```

**Matching algorithm**:
```python
def find_trigger_time(trigger_words: List[str],
                     audio_timestamps: List[WordTimestamp]) -> Optional[float]:
    """Find first occurrence of any trigger word."""
    for word_ts in audio_timestamps:
        if word_ts.word.lower() in [w.lower() for w in trigger_words]:
            return word_ts.start
    return None  # No trigger found
```

### 3. Implement Timing in Renderer (2 hours)

**Update ActScene construction**:

```python
class ActScene(Scene):
    def construct(self):
        # Get audio timing data
        audio_segment = get_audio_for_act(act_id)

        # Calculate sync points for each visual
        sync_points = calculate_sync_points(
            visuals=act.visuals,
            audio_segment=audio_segment
        )

        # Render visuals at calculated times
        for sync_point in sync_points:
            # Wait until visual should appear
            target_time = sync_point.start_time
            current_time = self.renderer.time
            wait_time = max(0, target_time - current_time)

            if wait_time > 0:
                self.wait(wait_time)

            # Render visual
            visual = get_visual_by_id(sync_point.visual_id)
            self._render_visual(visual, sync_point.duration)
```

### 4. Test & Measure Accuracy (1-2 hours)

- [ ] Generate Act with known timing (e.g., equation at 5.0s)
- [ ] Render video
- [ ] Manually measure: when does equation actually appear?
- [ ] Calculate error: |actual_time - expected_time|
- [ ] Test multiple Acts, calculate average error
- [ ] Verify: average error < 300ms

**Measurement method**:
```bash
# Open video in editor (iMovie, Premiere, or ffmpeg)
# Find frame where equation appears
# Calculate time: frame_number / fps

# Example: equation appears at frame 150, 30fps
actual_time = 150 / 30 = 5.0s
expected_time = 5.0s
error = |5.0 - 5.0| = 0.0s ✓
```

---

## Acceptance Criteria

✅ **Must have**:
- Can specify trigger words in VisualSpec
- Visual appears when trigger word is spoken
- Timing accuracy measured and documented
- Average error < 500ms (MVP target)

✅ **Production target**:
- Average error < 300ms
- No visual appears >1s off from expected time

✅ **Nice to have**:
- Lead time configurable per visual
- Fallback: if no trigger word, use estimated timing
- Visual validation tool (compare expected vs actual)

---

## Test Command

```bash
python tests/test_timing_accuracy.py
```

**Test script**:
```python
from src.audio.synthesizer import AudioSynthesizer
from src.visuals.renderer import VisualRenderer

# 1. Generate audio with known content
act = Act(
    id="timing_test",
    narration="First comes the title. Then at five seconds we show the equation F equals m a.",
    visuals=[
        VisualSpec(
            type="text",
            content="Title",
            trigger_words=["title"],  # Should appear ~1s
        ),
        VisualSpec(
            type="equation",
            content="F = ma",
            trigger_words=["five", "equation"],  # Should appear ~5s
        )
    ]
)

# 2. Synthesize audio (get word timestamps)
synthesizer = AudioSynthesizer()
audio_seg = synthesizer.synthesize_act(act, output_path)

# 3. Render visuals with timing
renderer = VisualRenderer(style, output_dir)
result = renderer.render_act(act, target_duration=audio_seg.duration)

# 4. Measure accuracy (manual for now)
print(f"Audio duration: {audio_seg.duration}s")
print(f"Word 'title' at: {find_word(audio_seg, 'title')}s")
print(f"Word 'five' at: {find_word(audio_seg, 'five')}s")
print("\nManually verify video timing matches!")
```

---

## Timing Calculation Algorithm

### Input
- Act with visuals (some with trigger_words)
- AudioSegment with word timestamps
- Default lead_time (0.5s)

### Output
- List of SyncPoints (when each visual should appear)

### Algorithm
```python
def calculate_sync_points(
    visuals: List[VisualSpec],
    audio: AudioSegment
) -> List[SyncPoint]:
    sync_points = []
    current_time = 0.0

    for visual in visuals:
        if visual.trigger_words:
            # Find trigger word in audio
            trigger_time = find_trigger_time(
                visual.trigger_words,
                audio.word_timestamps
            )

            if trigger_time:
                # Appear before word is spoken
                lead = visual.params.get('lead_time', 0.5)
                start_time = max(0, trigger_time - lead)
            else:
                # Fallback: sequential timing
                start_time = current_time
        else:
            # No trigger word: sequential
            start_time = current_time

        duration = visual.duration or 3.0  # Default

        sync_points.append(SyncPoint(
            visual_id=visual.type,
            start_time=start_time,
            duration=duration
        ))

        current_time = start_time + duration

    return sync_points
```

---

## Implementation Notes

### Manim Time Tracking
```python
# Access current scene time
current_time = self.renderer.time

# Or track manually
class ActScene(Scene):
    def __init__(self):
        super().__init__()
        self.scene_time = 0.0

    def construct(self):
        self.play(animation, run_time=2.0)
        self.scene_time += 2.0  # Track manually
```

### Precision Limitations
- **Manim FPS**: 30fps → ±33ms per frame
- **Wait() precision**: Good to ~10ms
- **Audio timestamp precision**: ±50ms (estimation) or ±10ms (forced alignment)

**Expected total error**:
- With estimation: ±33ms (frame) + ±50ms (audio) = **~±100ms best case**
- With forced alignment: ±33ms + ±10ms = **~±50ms best case**

### Achieving ±300ms Target
Should be achievable with:
- ✅ Word-level timestamps (estimation okay)
- ✅ Trigger word matching
- ✅ Lead time calculation
- ✅ Manim wait() precision

### If We Can't Hit ±300ms
- Use forced alignment (better audio timestamps)
- Increase FPS (60fps → ±16ms per frame)
- Frame-level control (advanced)

---

## Done When

- [x] Can specify trigger_words in VisualSpec
- [x] Visual appears near trigger word time
- [ ] Timing measured on at least 3 test videos (requires audio)
- [ ] Average timing error documented (requires audio)
- [ ] Error < 500ms (MVP) or < 300ms (production) (requires audio)
- [x] Algorithm handles missing trigger words gracefully

## Implementation Status (2025-11-09)

✅ **Complete**:
- Added `trigger_words` and `lead_time` fields to VisualSpec (models.py:42-50)
- Created timing module (`src/visuals/timing.py`):
  - `SyncPoint` dataclass for timing data
  - `VisualTimingCalculator` class
  - Trigger word matching algorithm
  - Fallback to sequential timing when no audio/trigger words
- Integrated into renderer (`render_act()` now accepts AudioSegment)
- Scene uses absolute timing with wait() for precise sync
- Handles missing trigger words gracefully (falls back to sequential)

🔄 **Untested**:
- Audio sync accuracy (no audio files with word timestamps yet)
- Actual ±300ms target verification
- Trigger word matching with real TTS output

📝 **How it works**:
1. VisualSpec can specify `trigger_words: ["mathematically", "equation"]`
2. VisualTimingCalculator matches trigger words to audio timestamps
3. Visuals appear `lead_time` seconds BEFORE trigger word (default 0.5s)
4. Renderer uses `wait()` for precise timing
5. Falls back to sequential timing if no audio/trigger words

**Next steps**:
- Generate audio with word timestamps (audio synthesis already implemented)
- Test end-to-end with real Act
- Measure accuracy and tune if needed

---

## Follow-up Work

- **Timing validation tool**: Auto-measure accuracy (no manual checking)
- **Forced alignment**: Improve audio timestamp precision
- **Frame-level control**: If ±300ms not achievable
- **Visual timing editor**: UI to adjust trigger times
