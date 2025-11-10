# E2E-001: ffmpeg Integration & Basic Assembly

**Priority**: P0 - Critical Path
**Estimate**: 3-4 hours (Actual: ~45 min)
**Dependencies**: None (ffmpeg system dependency)
**Status**: 🟢 Complete

---

## Goal

Get ffmpeg working to combine audio + video files into final MP4.

---

## Why This Matters

This is the foundation for video assembly. Without ffmpeg working, we can't create final videos. Everything else depends on this.

---

## Current State

- Audio synthesis creates MP3 files
- Visual rendering creates MP4 files
- No way to combine them

---

## Tasks

### 1. Check ffmpeg Installation (30 min)
- [ ] Test ffmpeg is installed and accessible
- [ ] Verify version supports needed features
- [ ] Document installation if missing
- [ ] Test basic ffmpeg command

**Test command**:
```bash
ffmpeg -version
```

**Expected**: ffmpeg version 5.0+ or similar

---

### 2. Create Compositor Module (1 hour)
- [ ] Create `src/assembly/compositor.py`
- [ ] Implement basic file checking
- [ ] Add logging for debug
- [ ] Handle temp file management

**Module structure**:
```python
from pathlib import Path
from typing import Optional
import subprocess
import logging

class VideoCompositor:
    """Assembles final video from audio + visual components."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def combine_audio_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        resolution: tuple = (1920, 1080)
    ) -> Path:
        """Combine single video + audio into MP4."""
        pass
```

---

### 3. Implement Simple Audio+Video Combine (1-1.5 hours)
- [ ] Build ffmpeg command
- [ ] Run subprocess
- [ ] Handle errors
- [ ] Verify output exists
- [ ] Test with sample files

**ffmpeg command**:
```bash
ffmpeg -y -i video.mp4 -i audio.mp3 \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 128k \
  -map 0:v:0 -map 1:a:0 \
  output.mp4
```

**Parameters**:
- `-y`: Overwrite output
- `-c:v libx264`: H.264 video codec
- `-preset medium`: Balance speed/quality
- `-crf 23`: Quality (lower = better, 18-28 range)
- `-c:a aac`: AAC audio codec
- `-b:a 128k`: Audio bitrate
- `-map`: Specify which streams to use

---

### 4. Test with Real Files (30 min)
- [ ] Use output from VIS-008 test (composition test)
- [ ] Use audio from audio synthesis example
- [ ] Combine them
- [ ] Play result in VLC/QuickTime
- [ ] Verify quality acceptable

**Test script**:
```python
from src.assembly.compositor import VideoCompositor
from pathlib import Path

compositor = VideoCompositor(Path("test_output/assembly"))

# Use existing test files
video = Path("src/visuals/test_output/composition/test_composition.mp4")
audio = Path("projects/test/audio/act_1.mp3")  # From audio example

output = compositor.combine_audio_video(
    video_path=video,
    audio_path=audio,
    output_path=Path("test_output/assembly/combined.mp4")
)

print(f"✓ Combined video: {output}")
print(f"✓ File size: {output.stat().st_size} bytes")
```

---

### 5. Add Quality Settings (30 min)
- [ ] Support different resolutions (1080p, 720p, 480p)
- [ ] Support quality presets (high, medium, low)
- [ ] Map to ffmpeg parameters
- [ ] Test each preset

**Quality presets**:
```python
QUALITY_PRESETS = {
    "low": {
        "resolution": (854, 480),
        "video_bitrate": "1M",
        "crf": 28,
        "preset": "fast"
    },
    "medium": {
        "resolution": (1280, 720),
        "video_bitrate": "2.5M",
        "crf": 23,
        "preset": "medium"
    },
    "high": {
        "resolution": (1920, 1080),
        "video_bitrate": "5M",
        "crf": 20,
        "preset": "slow"
    }
}
```

---

## Acceptance Criteria

✅ **Must have**:
- ffmpeg runs successfully from Python
- Can combine single audio + single video
- Output MP4 plays in video players
- Audio and video both present in output
- Quality is acceptable (not pixelated/garbled)

✅ **Nice to have**:
- Multiple quality presets work
- Temp files cleaned up
- Progress reporting from ffmpeg
- Good error messages on failure

---

## Test Command

```bash
python tests/test_compositor.py
```

**Test script** (create this):
```python
from src.assembly.compositor import VideoCompositor
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

def test_basic_combine():
    """Test combining audio + video"""
    compositor = VideoCompositor(Path("test_output/assembly"))

    # Use existing test files
    video = Path("src/visuals/test_output/composition/test_composition.mp4")
    audio = Path("projects/test/audio/act_1.mp3")

    if not video.exists():
        print("✗ Video file not found. Run VIS-008 test first.")
        return False

    if not audio.exists():
        print("✗ Audio file not found. Run audio synthesis example first.")
        return False

    try:
        output = compositor.combine_audio_video(
            video_path=video,
            audio_path=audio,
            output_path=Path("test_output/assembly/combined.mp4")
        )

        if output.exists():
            print(f"✓ Combined video created: {output}")
            print(f"✓ File size: {output.stat().st_size} bytes")
            return True
        else:
            print("✗ Output file not created")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_combine()
    exit(0 if success else 1)
```

---

## Blockers / Risks

**Blocker**: ffmpeg not installed
- **Solution**: `brew install ffmpeg` (macOS) or equivalent
- **Check**: `which ffmpeg`

**Risk**: ffmpeg version too old or missing codecs
- **Mitigation**: Document minimum version (5.0+)
- **Check**: `ffmpeg -codecs | grep h264` and `ffmpeg -codecs | grep aac`

**Risk**: Subprocess hangs or fails silently
- **Mitigation**: Add timeout, capture stderr, check return code

---

## Implementation Notes

### Error Handling Pattern

```python
def run_ffmpeg(args: list, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run ffmpeg with proper error handling."""
    cmd = ["ffmpeg", "-y", "-loglevel", "warning"] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout
        )
        return result

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"ffmpeg failed (exit code {e.returncode}):\n{e.stderr}"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffmpeg timed out after {timeout}s")
```

### File Validation

```python
def validate_input_files(video: Path, audio: Path):
    """Check input files exist and are valid."""
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")

    if not audio.exists():
        raise FileNotFoundError(f"Audio not found: {audio}")

    if video.stat().st_size == 0:
        raise ValueError(f"Video file is empty: {video}")

    if audio.stat().st_size == 0:
        raise ValueError(f"Audio file is empty: {audio}")
```

### Getting File Duration

```python
def get_duration(file_path: Path) -> float:
    """Get media file duration using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())
```

---

## Done When

- [x] ffmpeg command runs from Python
- [x] Can combine test audio + test video
- [x] Output MP4 created and plays correctly
- [x] Both audio and video present
- [x] Quality settings work (at least medium)
- [x] Test script passes

---

## Follow-up Stories

- **E2E-002**: Act Stitching (combine multiple videos)
- **E2E-003**: Audio-Visual Alignment (duration matching)

## Implementation Status (2025-11-09)

✅ **Complete**:
- ffmpeg 8.0 installed and verified
- Created `src/assembly/compositor.py` module:
  - `VideoCompositor` class with quality presets
  - `combine_audio_video()` - merge audio + video
  - `stitch_acts()` - concatenate multiple videos
  - `get_duration()` - query media duration
  - Error handling and validation
- Created `tests/test_compositor.py`
- Generated test audio file using macOS `say` command
- All tests passing

📝 **Test Results**:
- ✅ Basic audio+video combine: 104KB output, 5.2s duration
- ✅ Video stitching: 207KB output, 10.4s duration (2x original)
- Both tests verify correct duration and file creation

**Quality presets implemented**:
- Low: 480p, 1Mbps, fast encoding
- Medium: 720p, 2.5Mbps, balanced
- High: 1080p, 5Mbps, slow/quality

**Files created**:
- `src/assembly/__init__.py`
- `src/assembly/compositor.py` (~300 lines)
- `tests/test_compositor.py`
- `test_output/assembly/combined.mp4` (test output)
- `test_output/assembly/stitched.mp4` (test output)
