# VIS-001: Manim Executor Validation

**Priority**: P0 - Critical Path
**Estimate**: 3-4 hours (Actual: ~30 min)
**Dependencies**: None
**Status**: 🟢 Complete

---

## Goal

Validate that we can programmatically render Manim scenes and get video output.

---

## Why This Matters

This is the foundation. If the programmatic approach doesn't work, we need to know early so we can switch to CLI-based rendering.

---

## Current State

- `src/visuals/executor.py` exists with two approaches:
  1. Programmatic: Use Manim's Python API directly
  2. CLI: Write temp .py files and invoke `manim` command
- Neither approach has been tested

---

## Tasks

### 1. Test Programmatic Approach (2 hours)
- [ ] Create minimal test scene (just a circle)
- [ ] Configure Manim settings (resolution, FPS, output dir)
- [ ] Call `scene.render()` programmatically
- [ ] Verify MP4 file is created
- [ ] Check video plays correctly

**Test code**:
```python
from manim import Scene, Circle, Create, config as manim_config

# Configure
manim_config.pixel_width = 1920
manim_config.pixel_height = 1080
manim_config.frame_rate = 30
manim_config.quality = "medium_quality"

# Scene
class TestScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
        self.wait(1)

# Render
scene = TestScene()
scene.render()

# Check output exists
```

### 2. Handle Manim API Issues (1 hour)
If programmatic approach fails:
- [ ] Research Manim's current programmatic API
- [ ] Check Manim documentation for rendering examples
- [ ] Look for version compatibility issues

### 3. Implement CLI Fallback (1 hour, if needed)
If programmatic doesn't work:
- [ ] Implement `render_scene_via_cli()` in executor.py
- [ ] Write scene code to temp .py file
- [ ] Invoke: `manim -qm temp_file.py SceneName`
- [ ] Parse output to find rendered file path

---

## Acceptance Criteria

✅ **Must have**:
- Can render a simple Manim scene (circle) to MP4
- Output file exists at expected path
- Video plays in VLC/QuickTime
- Can specify quality (low/medium/high)

✅ **Nice to have**:
- Programmatic approach works (cleaner)
- Can capture Manim's progress output
- Can specify output filename

---

## Test Command

```bash
python src/visuals/executor.py
```

**Expected output**:
```
Test render successful: test_output/test_circle.mp4
```

**Manual verification**:
```bash
# Check file exists
ls test_output/test_circle.mp4

# Play video
open test_output/test_circle.mp4  # macOS
# or
vlc test_output/test_circle.mp4   # Linux
```

---

## Decision Points

**Question**: Which rendering approach to use?
- **Option A**: Programmatic (cleaner, direct Python integration)
- **Option B**: CLI-based (more robust, guaranteed to work)

**✅ DECISION**: Start with programmatic (Option A), fallback to CLI if needed
- Try programmatic first (2 hour time-box)
- If issues arise, switch to CLI approach
- Both implementations in executor.py for flexibility

---

## Blockers / Risks

**Blocker**: Manim may need LaTeX installed
- **Solution**: Document installation requirements
- macOS: `brew install --cask mactex`
- Linux: `sudo apt-get install texlive-full`

**Blocker**: Manim version compatibility
- **Solution**: Document tested Manim version (0.19.0)

**Risk**: Programmatic API may be unstable
- **Mitigation**: CLI fallback available

---

## Implementation Notes

### Manim Configuration Keys
```python
manim_config.pixel_width = 1920
manim_config.pixel_height = 1080
manim_config.frame_rate = 30
manim_config.quality = "medium_quality"  # or "low_quality", "high_quality"
manim_config.output_file = "output_name"
manim_config.media_dir = "path/to/media"
manim_config.video_dir = "path/to/videos"
manim_config.background_color = "#000000"
```

### Quality Settings
- `low_quality`: 480p, 15fps (fast preview)
- `medium_quality`: 720p, 30fps (good balance)
- `high_quality`: 1080p, 60fps (final output)

### Scene Rendering
```python
# Approach 1: Direct render
scene = MyScene()
scene.render()

# Approach 2: Using Manim's renderer
from manim import tempconfig
with tempconfig({"quality": "medium_quality"}):
    scene = MyScene()
    scene.render()
```

---

## Done When

- [x] Can render circle test scene
- [x] Output MP4 plays correctly
- [x] Can control quality settings
- [x] Know which approach (programmatic vs CLI) to use
- [x] `src/visuals/executor.py` updated with working implementation
- [x] Test passes: `python src/visuals/executor.py`

---

## Follow-up Stories

- **VIS-002**: Use executor to render more complex scene (text + shape)
- **VIS-003**: Integrate StyleConfig into Manim configuration
