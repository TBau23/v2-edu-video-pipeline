# End-to-End Integration - Story Breakdown

Breaking down Phase 2 (E2E Integration) into testable, deliverable stories.

## Overview

**Goal**: Prompt → final video (even if sync is rough)

**Current state**:
- ✅ Script generation works
- ✅ Audio synthesis works
- ✅ Visual rendering works (Manim)
- ❌ No way to combine them into final video

**Target state**: Can run one command and get a complete video with audio + visuals

---

## Story Structure

Each story includes:
- **Story ID**: Unique identifier
- **Title**: What we're building
- **Why**: Value/purpose
- **Tasks**: Concrete steps
- **Acceptance Criteria**: How to verify it works
- **Estimate**: Time to complete
- **Dependencies**: What must be done first
- **Test Command**: How to validate

---

## Stories by Priority

### Core Infrastructure (Week 1)

**E2E-001: ffmpeg Integration & Basic Assembly**
**E2E-002: Act Stitching**
**E2E-003: Audio-Visual Alignment**

### Integration & Testing (Week 2)

**E2E-004: End-to-End Pipeline Script**
**E2E-005: Error Handling & Validation**
**E2E-006: Progress Reporting**

---

## Dependencies Graph

```
VIS-001 to VIS-009 (Manim) ──┐
Audio Synthesis ─────────────┼──→ E2E-001 (ffmpeg basics)
                             │         ↓
                             └──→ E2E-002 (stitching)
                                       ↓
                                  E2E-003 (alignment)
                                       ↓
                                  E2E-004 (pipeline)
                                       ↓
                                  E2E-005 (errors) + E2E-006 (progress)
```

**Critical path**: E2E-001 → E2E-002 → E2E-003 → E2E-004

---

## Story Details

### E2E-001: ffmpeg Integration & Basic Assembly
**Priority**: P0 - Critical Path
**Estimate**: 3-4 hours
**Dependencies**: None (ffmpeg system dependency)
**Status**: 🔴 Not Started

**Goal**: Get ffmpeg working to combine audio + video files

**Tasks**:
1. Test ffmpeg installation
2. Create basic compositor module
3. Combine single audio + single video
4. Verify output MP4 plays correctly
5. Test quality settings (resolution, bitrate)

**Test case**:
```python
# Input: one audio file + one video file
# Output: MP4 with audio track
compositor.combine_simple(
    audio="test.mp3",
    video="test.mp4",
    output="result.mp4"
)
```

**Acceptance criteria**:
- ffmpeg subprocess runs successfully
- Output MP4 has both audio and video
- Plays in VLC/QuickTime
- Can specify output resolution

**Blockers**:
- ffmpeg must be installed (`brew install ffmpeg`)

See: `planning/stories/E2E-001-ffmpeg-integration.md`

---

### E2E-002: Act Stitching
**Priority**: P0 - Critical Path
**Estimate**: 2-3 hours
**Dependencies**: E2E-001
**Status**: 🔴 Not Started

**Goal**: Combine multiple Act videos sequentially into one video

**Tasks**:
1. Implement multi-video concatenation
2. Handle different Act durations
3. Add transitions between Acts (optional fade)
4. Test with 3+ Acts
5. Verify no gaps/overlaps

**Test case**:
```python
# Input: 3 Act videos
# Output: Single video with all 3 Acts
compositor.stitch_acts([
    "act_1.mp4",
    "act_2.mp4",
    "act_3.mp4"
], output="full_video.mp4")
```

**Acceptance criteria**:
- Multiple videos combined sequentially
- No visual glitches at boundaries
- Audio plays continuously
- Total duration = sum(act durations)

**Implementation note**: Use ffmpeg concat demuxer or filter

See: `planning/stories/E2E-002-act-stitching.md`

---

### E2E-003: Audio-Visual Alignment
**Priority**: P0 - Critical Path
**Estimate**: 4-5 hours
**Dependencies**: E2E-001, VIS-009 (timing)
**Status**: 🔴 Not Started

**Goal**: Match visual timing to audio duration precisely

**Tasks**:
1. Calculate visual duration vs audio duration
2. Pad/trim video to match audio
3. Handle timing mismatches (visual too short/long)
4. Test with various duration ratios
5. Ensure audio-visual sync maintained

**Key challenge**: Visual might render to 7.3s but audio is 8.0s
- Solution: Pad with final frame hold or black screen

**Test case**:
```python
# Audio: 8.0s, Video: 7.3s
# Should pad video to 8.0s
compositor.align_durations(
    audio="narration.mp3",  # 8.0s
    video="visuals.mp4",    # 7.3s
    output="aligned.mp4"    # 8.0s
)
```

**Acceptance criteria**:
- Audio duration always matches video duration
- No audio cut-off
- Visual holds last frame if too short
- Smooth padding (not abrupt)

See: `planning/stories/E2E-003-alignment.md`

---

### E2E-004: End-to-End Pipeline Script
**Priority**: P0 - Critical Path
**Estimate**: 3-4 hours
**Dependencies**: E2E-001, E2E-002, E2E-003, Audio, Visuals
**Status**: 🔴 Not Started

**Goal**: Single script that runs full pipeline: prompt → video

**Tasks**:
1. Create orchestrator module
2. Chain all steps: script → audio → visuals → assembly
3. Handle intermediate file management
4. Save artifacts to workspace
5. Return final video path

**Pipeline stages**:
```
Prompt → Script Generation
       → Audio Synthesis (per Act)
       → Visual Rendering (per Act)
       → Video Assembly
       → Final MP4
```

**Test case**:
```bash
python examples/generate_video.py \
  --prompt "Explain Newton's First Law" \
  --output projects/newtons_first
```

**Expected output**:
```
projects/newtons_first/
  script.json
  audio/
    act_1.mp3
    act_2.mp3
    ...
  visuals/
    act_1.mp4
    act_2.mp4
    ...
  final_video.mp4  # ← The result!
```

**Acceptance criteria**:
- One command produces complete video
- All intermediate files saved
- Final video has narration + visuals
- Duration matches audio
- Can replay pipeline from saved artifacts

See: `planning/stories/E2E-004-pipeline.md`

---

### E2E-005: Error Handling & Validation
**Priority**: P1 - High Priority
**Estimate**: 2-3 hours
**Dependencies**: E2E-004
**Status**: 🔴 Not Started

**Goal**: Graceful error handling throughout pipeline

**Tasks**:
1. Check dependencies (ffmpeg, API keys, LaTeX)
2. Validate inputs (prompt not empty, etc.)
3. Catch and report errors with helpful messages
4. Implement retry logic for API calls
5. Clean up temp files on failure

**Error scenarios to handle**:
- Missing API key
- ffmpeg not installed
- TTS API failure
- Manim rendering failure
- Disk space issues

**Test case**: Run pipeline with missing dependencies

**Acceptance criteria**:
- Clear error messages (not stack traces)
- Tells user what to fix
- Cleans up partial files
- Retries transient failures

See: `planning/stories/E2E-005-errors.md`

---

### E2E-006: Progress Reporting
**Priority**: P2 - Nice to Have
**Estimate**: 2-3 hours
**Dependencies**: E2E-004
**Status**: 🔴 Not Started

**Goal**: Show user what's happening during long operations

**Tasks**:
1. Add progress logging to each stage
2. Estimate total time
3. Show current step (1/5: Generating script...)
4. Progress bars for rendering
5. Summary at end (duration, file size, etc.)

**Expected output**:
```
[1/5] Generating script... ✓ (3.2s)
[2/5] Synthesizing audio...
  - Act 1: ✓ (2.1s)
  - Act 2: ✓ (1.9s)
  - Act 3: ✓ (2.3s)
[3/5] Rendering visuals...
  - Act 1: ████████████░░░░ 75%
```

**Acceptance criteria**:
- User can see progress
- Estimated time remaining
- Clear indication of current step
- Works for both fast and slow operations

See: `planning/stories/E2E-006-progress.md`

---

## MVP Milestone

**Definition of MVP**: One command generates complete video

**Required stories**: E2E-001, E2E-002, E2E-003, E2E-004

**Estimated time**: 12-16 hours

**Test case**:
```bash
python examples/generate_video.py \
  --prompt "Explain F=ma with a car example"
```

**Expected result**:
- 30-60 second video
- Narration explaining the concept
- Visual showing equation
- Animation of car (if implemented)
- Audio and visuals reasonably synced (±1s acceptable for MVP)

**Success criteria**:
- Video file created
- Plays without errors
- Includes both audio and visuals
- Content matches prompt

---

## Full Feature Milestone

**Definition**: Production-ready pipeline with error handling

**Required stories**: All E2E-001 through E2E-006

**Test case**: Generate 3 different videos successfully

---

## Key Design Decisions

### Decision 1: ffmpeg vs Python Video Libraries

**Question**: Use ffmpeg subprocess or Python library (moviepy)?

**✅ DECISION**: ffmpeg subprocess

**Why**:
- More control over encoding settings
- Better performance
- Industry standard
- Avoid Python library dependencies

**Trade-off**: More complex subprocess handling

---

### Decision 2: Timing Strategy

**Question**: How to handle visual duration ≠ audio duration?

**✅ DECISION**: Pad video to match audio duration

**Approach**:
- If video too short: hold last frame
- If video too long: trim (but log warning)
- Never cut audio

**Why**: Audio is primary content, video supports it

---

### Decision 3: Intermediate File Management

**Question**: Keep all intermediate files or clean up?

**✅ DECISION**: Keep everything for MVP

**Why**:
- Debugging easier
- Can re-run parts of pipeline
- Disk space not a concern for MVP
- Can add cleanup later as optimization

**Structure**:
```
projects/{project_id}/
  script.json
  audio/
  visuals/
  final_video.mp4
```

---

## Risk Mitigation

**Risk**: ffmpeg timing precision insufficient
**Mitigation**: Start with simple concat, can add frame-level control later

**Risk**: Audio-visual sync still rough after E2E-003
**Mitigation**: Acceptable for MVP, Phase 3 (VIS-009) handles precision

**Risk**: Large video files consume disk space
**Mitigation**: Use reasonable quality settings, document requirements

---

## Success Metrics

**After E2E-001 to E2E-003**:
- ✅ Can combine audio + video files
- ✅ Multiple Acts stitch together
- ✅ Durations match correctly

**After E2E-004**:
- ✅ One command produces complete video
- ✅ Prompt → video works end-to-end
- ✅ Video quality acceptable

**After E2E-005 to E2E-006**:
- ✅ Errors handled gracefully
- ✅ Progress visible to user
- ✅ Pipeline feels polished

---

## Implementation Notes

### ffmpeg Basic Commands

**Combine audio + video**:
```bash
ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
```

**Concatenate videos**:
```bash
# Create concat.txt
echo "file 'act_1.mp4'" > concat.txt
echo "file 'act_2.mp4'" >> concat.txt

ffmpeg -f concat -safe 0 -i concat.txt -c copy output.mp4
```

**Pad video to duration**:
```bash
ffmpeg -i video.mp4 -i audio.mp3 \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=<padding>[v]" \
  -map "[v]" -map 1:a output.mp4
```

### Python Subprocess Pattern

```python
import subprocess
from pathlib import Path

def run_ffmpeg(args: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run ffmpeg command safely."""
    cmd = ["ffmpeg", "-y"] + args  # -y to overwrite

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    return result
```

---

## How to Use This Plan

1. **Read story details** in `planning/stories/E2E-XXX.md`
2. **Work on one story at a time** (follow critical path)
3. **Test after each story** using the test command
4. **Mark complete** when acceptance criteria met
5. **Update estimates** based on actual time

**Recommended order**:
1. E2E-001 (ffmpeg basics)
2. E2E-002 (stitching)
3. E2E-003 (alignment)
4. E2E-004 (pipeline)
5. E2E-005 (errors)
6. E2E-006 (progress)

---

## Next Steps

**Immediate**: Start with E2E-001 (ffmpeg integration)
- Test ffmpeg installation
- Create compositor module
- Combine simple audio + video

**After MVP**:
- Phase 3: Timing precision (±300ms)
- Phase 4: Animation library expansion
- Phase 5: Polish & UX
