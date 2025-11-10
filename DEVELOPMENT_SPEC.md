# Development Spec - Remaining Work

Breaking down what needs to be built, in priority order.

## Phase 1: Visual Rendering MVP (Critical Path)

**Goal**: Get Manim actually rendering videos from VisualSpecs

**Priority**: HIGHEST - blocks everything else

### 1.1 Test Basic Manim Integration
**Estimate**: 2-4 hours
**Tasks**:
- [ ] Validate `src/visuals/executor.py` works with Manim's API
- [ ] Test rendering simple scene (circle, text)
- [ ] Confirm output MP4 files are created
- [ ] Test quality settings (low/medium/high)

**Acceptance criteria**: Can render a basic Manim scene to MP4 file

**Blockers**:
- May need LaTeX installed for equations
- May need to adjust Manim programmatic API approach
- Might need to fall back to CLI-based rendering

### 1.2 Equation Rendering
**Estimate**: 2-3 hours
**Tasks**:
- [ ] Test LaTeX → MathTex rendering
- [ ] Verify Write animation for equations
- [ ] Test positioning (center, top, bottom)
- [ ] Validate timing control (run_time parameter)

**Test case**: Render `F = ma` equation with write animation

### 1.3 Text Rendering
**Estimate**: 1-2 hours
**Tasks**:
- [ ] Test Text mobject with styling
- [ ] Verify font size, color from StyleConfig
- [ ] Test fade vs write animations
- [ ] Test positioning

**Test case**: Render title text "Newton's First Law"

### 1.4 Graph Rendering
**Estimate**: 3-4 hours
**Tasks**:
- [ ] Complete function plotting (not just axes)
- [ ] Parse `function` param (string → lambda)
- [ ] Test axis labels and ranges
- [ ] Test animation (draw axes, then plot)

**Test case**: Plot `y = 5x` with labeled axes

### 1.5 Animation Integration
**Estimate**: 4-6 hours
**Tasks**:
- [ ] Test animation library functions return valid Manim objects
- [ ] Fix `car_accelerating` animation
- [ ] Fix `hockey_puck_sliding` animation
- [ ] Test parameter passing (VisualSpec params → animation kwargs)
- [ ] Add at least 2 more physics animations

**Test case**: Render car accelerating animation with motion lines

**Deliverable**: Can render a simple Act with equation + text + animation

---

## Phase 2: End-to-End Integration (Critical Path)

**Goal**: Prompt → final video (even if sync is rough)

**Priority**: HIGH - need to validate full pipeline

### 2.1 Build Video Assembly System
**Estimate**: 6-8 hours
**Location**: `src/assembly/compositor.py`

**Tasks**:
- [ ] ffmpeg integration (Python subprocess)
- [ ] Stitch Act videos sequentially
- [ ] Add audio track
- [ ] Basic sync (visuals start when audio starts)
- [ ] Output 1080p MP4

**Key functions**:
```python
def assemble_video(
    audio_segments: List[AudioSegment],
    visual_paths: List[Path],
    output_path: Path
) -> Path:
    """Combine audio + visuals → final video"""
    pass
```

**Acceptance criteria**:
- Can take audio files + visual files → single MP4
- Audio plays correctly
- Visuals appear in order

### 2.2 Basic Synchronization
**Estimate**: 4-6 hours
**Location**: `src/assembly/sync.py`

**Tasks**:
- [ ] Calculate visual start times from audio timestamps
- [ ] Create ffmpeg timeline with precise timing
- [ ] Handle visual duration vs audio duration mismatches
- [ ] Add fade transitions between acts

**Key data structure**:
```python
@dataclass
class SyncPoint:
    visual_id: str
    audio_act_id: str
    start_time: float  # When to show this visual
    duration: float
    trigger_word: Optional[str]  # Word that triggers this visual
```

**Acceptance criteria**:
- Visuals appear roughly when mentioned in narration (±1s acceptable for now)

### 2.3 Create End-to-End Example
**Estimate**: 2-3 hours
**Location**: `examples/generate_video.py`

**Tasks**:
- [ ] Script that runs full pipeline: prompt → MP4
- [ ] Handle errors gracefully
- [ ] Show progress (which step is running)
- [ ] Save intermediate artifacts

**Usage**:
```bash
python examples/generate_video.py --prompt "Explain Newton's First Law"
```

**Deliverable**: Working end-to-end pipeline

---

## Phase 3: Timing Precision (Quality)

**Goal**: Hit ±300ms sync accuracy target

**Priority**: MEDIUM - needed for production quality

### 3.1 Implement Forced Alignment
**Estimate**: 8-12 hours
**Location**: `src/audio/timing.py`

**Tasks**:
- [ ] Research forced alignment tools (Gentle, aeneas, MFA)
- [ ] Choose tool (recommend: aeneas - pure Python, easy install)
- [ ] Integrate: audio file + text → word timestamps
- [ ] Test accuracy (should be ±50ms)
- [ ] Add as option (estimation vs forced alignment)

**Acceptance criteria**: Word timestamps accurate to ±50ms

### 3.2 Word-Triggered Visual Cues
**Estimate**: 4-6 hours
**Location**: `src/assembly/sync.py`

**Tasks**:
- [ ] Parse VisualSpec for trigger words
- [ ] Match trigger words to timestamps
- [ ] Calculate visual appearance time (word.start - lead_time)
- [ ] Generate precise ffmpeg timeline

**Example**:
```json
{
  "type": "equation",
  "content": "F = ma",
  "trigger_words": ["mathematically", "equation"],
  "lead_time": 0.5
}
```

Equation appears 0.5s before "mathematically" is spoken.

### 3.3 Measure Sync Accuracy
**Estimate**: 2-3 hours
**Location**: `tests/test_sync_accuracy.py`

**Tasks**:
- [ ] Automated test that measures sync
- [ ] Compare expected vs actual visual start times
- [ ] Report max error, average error, p95 error
- [ ] Validate ±300ms target

**Deliverable**: Quantified sync accuracy

---

## Phase 4: Animation Library Expansion (Quality)

**Goal**: Enough animations for diverse educational content

**Priority**: MEDIUM - needed for variety

### 4.1 Core Physics Animations
**Estimate**: 8-12 hours
**Location**: `src/visuals/animations.py`

**Animations to add**:
- [ ] Projectile motion (ball trajectory)
- [ ] Pendulum swing
- [ ] Spring oscillation
- [ ] Collision (elastic vs inelastic)
- [ ] Free fall with gravity
- [ ] Circular motion
- [ ] Force diagram builder (parameterized)

**Each animation needs**:
- Docstring explaining use case
- Parameters for customization
- Return: mobjects, animations, duration
- Registration in AnimationLibrary

### 4.2 Math Animations
**Estimate**: 6-8 hours

**Animations to add**:
- [ ] Number line operations
- [ ] Vector addition/subtraction
- [ ] Geometric transformations (rotation, scaling)
- [ ] Function transformation (shift, stretch)
- [ ] Derivative visualization
- [ ] Integral as area under curve

### 4.3 Diagram System
**Estimate**: 6-8 hours
**Location**: `src/visuals/diagrams.py`

**Build parameterized diagram generator**:
- [ ] Force diagrams (objects + force arrows + labels)
- [ ] Circuit diagrams (basic components)
- [ ] Geometric figures (labeled triangles, etc.)

**Example**:
```json
{
  "type": "diagram",
  "content": "force_diagram",
  "params": {
    "object": "box",
    "forces": [
      {"name": "Weight", "direction": "down", "magnitude": "mg", "color": "red"},
      {"name": "Normal", "direction": "up", "magnitude": "N", "color": "blue"}
    ]
  }
}
```

**Deliverable**: 15+ high-quality animations covering common physics/math scenarios

---

## Phase 5: Polish & UX (Nice-to-Have)

**Goal**: Make it production-ready

**Priority**: LOW - functional system is more important

### 5.1 Preview Mode
**Estimate**: 3-4 hours

**Tasks**:
- [ ] Low-res rendering (480p, lower FPS)
- [ ] Fast audio synthesis option
- [ ] Quick preview without full render
- [ ] Compare: preview vs final

**Value**: Fast iteration (30s preview vs 5min final render)

### 5.2 Progress & Error Handling
**Estimate**: 4-6 hours

**Tasks**:
- [ ] Progress bars for long operations
- [ ] Better error messages (not just stack traces)
- [ ] Retry logic for API failures
- [ ] Validation (check API keys, dependencies, etc.)

### 5.3 Batch Processing
**Estimate**: 4-6 hours
**Location**: `examples/batch_generate.py`

**Tasks**:
- [ ] Process multiple prompts from file
- [ ] Generate multiple videos in sequence
- [ ] Parallel audio synthesis
- [ ] Report generation (what succeeded/failed)

**Use case**: Generate all 3 Newton's Laws videos at once

### 5.4 Content Planning Layer
**Estimate**: 6-8 hours
**Location**: `src/planning/`

**Tasks**:
- [ ] LLM generates content structure before script
- [ ] User reviews/edits structure
- [ ] Then generates full script from approved structure
- [ ] Two-stage generation workflow

**Value**: More user control over content before committing to full generation

---

## Phase 6: Advanced Features (Future)

**Priority**: LOWEST - nice to have

- Web UI (Gradio or custom)
- Multiple style themes (light mode, colorful, etc.)
- Export to other formats (GIF, WebM)
- Subtitles/captions generation
- Multi-language support (TTS + translated narration)
- Interactive elements (for web embedding)

---

## Dependency Graph

```
Phase 1: Visual Rendering ─────┐
                              ↓
Phase 2: E2E Integration ─────┤
                              ↓
Phase 3: Timing Precision     │ (can be parallel)
Phase 4: Animation Library ───┘

Phase 5: Polish (depends on 1-4)
Phase 6: Advanced (depends on everything)
```

**Critical path**: Phase 1 → Phase 2
**Parallel work**: Phase 3 + Phase 4 can happen concurrently

---

## Next Steps (Immediate)

**For MVP (minimum viable product)**:
1. ✅ Fix visual rendering (Phase 1: 1.1 - 1.3)
2. ✅ Build video assembly (Phase 2: 2.1 - 2.2)
3. ✅ Test end-to-end (Phase 2: 2.3)

**Estimated time to MVP**: 20-30 hours

**Once MVP works**:
- Measure sync accuracy
- Expand animation library
- Implement forced alignment
- Polish UX

---

## How to Iterate on This Spec

1. **Pick a phase** (recommend: Phase 1 first)
2. **Break down tasks** into 1-2 hour chunks
3. **Test each task** before moving to next
4. **Update this spec** as you learn (add tasks, adjust estimates)
5. **Mark completed** with ✅

**Example workflow**:
- Day 1: Phase 1.1 + 1.2 (test Manim + equations)
- Day 2: Phase 1.3 + 1.4 (text + graphs)
- Day 3: Phase 1.5 (animations)
- Day 4: Phase 2.1 (video assembly)
- Day 5: Phase 2.2 + 2.3 (sync + E2E test)
- **Result**: Working MVP in 5 days

---

## Risk Assessment

**High Risk**:
- Manim programmatic API may not work as expected → May need CLI approach
- ffmpeg timing precision may be tricky → May need frame-level control
- Forced alignment accuracy may not hit ±50ms → May need better tool

**Medium Risk**:
- Animation parameter parsing complex → May need hand-tuning per animation
- LLM-generated visual specs may be inconsistent → May need prompt refinement

**Low Risk**:
- Audio synthesis (already validated)
- Workspace system (simple file I/O)
- Style system (just data)

---

## Success Metrics

**MVP Success** (end of Phase 2):
- Can generate a 60s video from a prompt
- Video has narration + visuals + equations
- Sync is "good enough" (visuals appear roughly when mentioned)

**Production Success** (end of Phase 3):
- Sync accuracy ±300ms (measured)
- Videos look professional
- Iteration workflow is smooth (edit script → regenerate in <5min)

**Complete Success** (end of Phase 4):
- 15+ animations covering common scenarios
- Can generate videos for diverse topics (physics, math, chemistry)
- Style system supports multiple themes
