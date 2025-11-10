# E2E-004: End-to-End Pipeline Script

**Priority**: P0 - Critical Path
**Estimate**: 3-4 hours
**Dependencies**: E2E-001 (ffmpeg), E2E-002 (stitching), E2E-003 (alignment), Audio, Visuals
**Status**: 🔴 Not Started

---

## Goal

Create single script that orchestrates full pipeline: prompt → final video

---

## Why This Matters

This is the **magic moment** - when all the pieces come together. This proves the system works end-to-end and gives us something to demo and iterate on.

---

## Current State

- Script generation: ✅ Works
- Audio synthesis: ✅ Works
- Visual rendering: ✅ Works
- Video assembly: ✅ Works (after E2E-001 to E2E-003)
- **Missing**: Orchestration to tie everything together

---

## Pipeline Stages

```
[1] User Prompt
      ↓
[2] Script Generation (LLM)
      ↓
[3] Audio Synthesis (per Act)
      ↓
[4] Visual Rendering (per Act)
      ↓
[5] Video Assembly
      ↓
[6] Final Video MP4
```

---

## Tasks

### 1. Create Orchestrator Module (1 hour)
- [ ] Create `src/pipeline/orchestrator.py`
- [ ] Define pipeline stages
- [ ] Handle intermediate artifacts
- [ ] Manage workspace directory

**Module structure**:
```python
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from src.primitives.models import Script, AudioSegment
from src.script.generator import generate_script
from src.audio.synthesizer import AudioSynthesizer
from src.visuals.renderer import VisualRenderer
from src.assembly.compositor import VideoCompositor

@dataclass
class PipelineResult:
    """Result of full pipeline execution."""
    video_path: Path
    script: Script
    duration: float
    workspace: Path


class VideoPipeline:
    """Orchestrates end-to-end video generation."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def generate(
        self,
        prompt: str,
        project_id: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> PipelineResult:
        """Run full pipeline: prompt → video."""
        pass
```

---

### 2. Implement Stage 1-2: Script Generation (30 min)
- [ ] Call script generator with prompt
- [ ] Save script.json to workspace
- [ ] Validate script has acts and visuals
- [ ] Log script details (number of acts, estimated duration)

**Code**:
```python
# Stage 1: Generate script
logger.info("Stage 1/5: Generating script...")
script = generate_script(
    user_prompt=prompt,
    api_key=openai_key
)

# Save to workspace
script_path = workspace / "script.json"
save_pretty_json(script.model_dump(), script_path)

logger.info(f"✓ Script generated: {len(script.acts)} acts")
```

---

### 3. Implement Stage 3: Audio Synthesis (1 hour)
- [ ] Synthesize audio for each Act
- [ ] Save to workspace/audio/
- [ ] Collect AudioSegment objects
- [ ] Handle TTS API failures gracefully

**Code**:
```python
# Stage 2: Synthesize audio
logger.info("Stage 2/5: Synthesizing audio...")

synthesizer = AudioSynthesizer(
    provider="openai",
    output_dir=workspace / "audio",
    api_key=openai_key
)

audio_segments = []
for i, act in enumerate(script.acts, 1):
    logger.info(f"  Synthesizing Act {i}/{len(script.acts)}...")

    audio_seg = synthesizer.synthesize_act(
        act=act,
        output_path=workspace / "audio" / f"{act.id}.mp3"
    )

    audio_segments.append(audio_seg)

logger.info(f"✓ Audio synthesized: {len(audio_segments)} files")
```

---

### 4. Implement Stage 4: Visual Rendering (1 hour)
- [ ] Render visuals for each Act
- [ ] Pass audio for timing sync
- [ ] Save to workspace/visuals/
- [ ] Collect video paths
- [ ] Handle Manim rendering failures

**Code**:
```python
# Stage 3: Render visuals
logger.info("Stage 3/5: Rendering visuals...")

renderer = VisualRenderer(
    style=StyleConfig.load_preset("default"),
    output_dir=workspace / "visuals"
)

visual_paths = []
for i, (act, audio) in enumerate(zip(script.acts, audio_segments), 1):
    logger.info(f"  Rendering Act {i}/{len(script.acts)}...")

    result = renderer.render_act(
        act=act,
        audio=audio
    )

    visual_paths.append(result.output_path)

logger.info(f"✓ Visuals rendered: {len(visual_paths)} files")
```

---

### 5. Implement Stage 5: Video Assembly (30 min)
- [ ] Combine audio + visuals for each Act
- [ ] Stitch all Acts together
- [ ] Save final video
- [ ] Verify output exists and is valid

**Code**:
```python
# Stage 4: Assemble video
logger.info("Stage 4/5: Assembling final video...")

compositor = VideoCompositor(workspace / "assembly")

# Combine each Act's audio + visuals
act_videos = []
for i, (audio, visual) in enumerate(zip(audio_segments, visual_paths), 1):
    logger.info(f"  Combining Act {i}/{len(audio_segments)}...")

    act_video = compositor.combine_audio_video(
        video_path=visual,
        audio_path=audio.audio_path,
        output_path=workspace / "assembly" / f"act_{i}.mp4"
    )
    act_videos.append(act_video)

# Stitch all Acts together
logger.info("  Stitching Acts...")
final_video = compositor.stitch_acts(
    videos=act_videos,
    output_path=workspace / "final_video.mp4"
)

logger.info(f"✓ Final video created: {final_video}")
```

---

### 6. Create CLI Script (30 min)
- [ ] Create `examples/generate_video.py`
- [ ] Add argparse for command-line args
- [ ] Load API keys from .env
- [ ] Call pipeline orchestrator
- [ ] Print results

**CLI script**:
```python
"""
Generate educational video from text prompt.

Usage:
    python examples/generate_video.py --prompt "Explain Newton's First Law"
"""

import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

from src.pipeline.orchestrator import VideoPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(
        description="Generate educational video from prompt"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Educational topic to explain"
    )
    parser.add_argument(
        "--project-id",
        help="Project ID (default: auto-generated)"
    )
    parser.add_argument(
        "--output",
        default="projects",
        help="Output directory (default: projects)"
    )

    args = parser.parse_args()

    # Load environment
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")

    if not openai_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        exit(1)

    # Run pipeline
    pipeline = VideoPipeline(Path(args.output))

    result = pipeline.generate(
        prompt=args.prompt,
        project_id=args.project_id,
        openai_key=openai_key
    )

    # Print results
    print("\n" + "=" * 60)
    print("✓ Video generation complete!")
    print("=" * 60)
    print(f"Video: {result.video_path}")
    print(f"Duration: {result.duration:.1f}s")
    print(f"Acts: {len(result.script.acts)}")
    print(f"Workspace: {result.workspace}")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

---

## Acceptance Criteria

✅ **Must have**:
- One command generates complete video from prompt
- All intermediate files saved to workspace
- Final video has narration + visuals
- Video duration matches audio
- Script runs without crashes

✅ **Nice to have**:
- Progress indication for each stage
- Estimated time remaining
- Can resume from saved artifacts
- Clear success/failure messages

---

## Test Command

```bash
python examples/generate_video.py \
  --prompt "Explain F=ma using a car accelerating" \
  --project-id test_fma
```

**Expected output**:
```
Stage 1/5: Generating script...
✓ Script generated: 3 acts

Stage 2/5: Synthesizing audio...
  Synthesizing Act 1/3...
  Synthesizing Act 2/3...
  Synthesizing Act 3/3...
✓ Audio synthesized: 3 files

Stage 3/5: Rendering visuals...
  Rendering Act 1/3...
  Rendering Act 2/3...
  Rendering Act 3/3...
✓ Visuals rendered: 3 files

Stage 4/5: Assembling final video...
  Combining Act 1/3...
  Combining Act 2/3...
  Combining Act 3/3...
  Stitching Acts...
✓ Final video created: projects/test_fma/final_video.mp4

============================================================
✓ Video generation complete!
============================================================
Video: projects/test_fma/final_video.mp4
Duration: 45.3s
Acts: 3
Workspace: projects/test_fma
============================================================
```

**Manual verification**:
```bash
# Play the video
open projects/test_fma/final_video.mp4

# Check it has:
# - Audio narration
# - Visual content
# - Equations (if applicable)
# - Reasonable quality
```

---

## Workspace Structure

After running pipeline:
```
projects/test_fma/
  script.json           # Generated script
  audio/
    act_1_intro.mp3
    act_2_explanation.mp3
    act_3_example.mp3
  visuals/
    act_1_intro.mp4
    act_2_explanation.mp4
    act_3_example.mp4
  assembly/
    act_1.mp4           # Audio + visual combined
    act_2.mp4
    act_3.mp4
  final_video.mp4       # ← The result!
```

---

## Blockers / Risks

**Blocker**: Any upstream stage fails (script gen, audio, visuals, assembly)
- **Mitigation**: Add error handling in each stage
- **See**: E2E-005 (Error Handling)

**Risk**: Pipeline takes very long (5+ minutes)
- **Mitigation**: Acceptable for MVP, optimize later
- **Future**: Parallel audio synthesis, caching

**Risk**: Large disk space usage
- **Mitigation**: Document requirements (~100MB per video)

---

## Implementation Notes

### Project ID Generation

```python
import hashlib
from datetime import datetime

def generate_project_id(prompt: str) -> str:
    """Generate project ID from prompt."""
    # Use first few words + timestamp
    words = prompt.lower().split()[:3]
    slug = "_".join(words)

    # Add hash for uniqueness
    hash_short = hashlib.md5(prompt.encode()).hexdigest()[:6]

    return f"{slug}_{hash_short}"
```

### Workspace Setup

```python
def setup_workspace(workspace_root: Path, project_id: str) -> Path:
    """Create workspace directory structure."""
    workspace = workspace_root / project_id

    # Create subdirectories
    (workspace / "audio").mkdir(parents=True, exist_ok=True)
    (workspace / "visuals").mkdir(parents=True, exist_ok=True)
    (workspace / "assembly").mkdir(parents=True, exist_ok=True)

    return workspace
```

### Stage Error Handling

```python
def safe_stage(stage_name: str, stage_func):
    """Run stage with error handling."""
    try:
        logger.info(f"Stage: {stage_name}")
        result = stage_func()
        logger.info(f"✓ {stage_name} complete")
        return result

    except Exception as e:
        logger.error(f"✗ {stage_name} failed: {e}")
        raise RuntimeError(f"Pipeline failed at: {stage_name}") from e
```

---

## Done When

- [x] Can run one command to generate video
- [x] Prompt → video pipeline works end-to-end
- [x] All stages execute in order
- [x] Intermediate files saved correctly
- [x] Final video created and playable
- [x] Test with at least 2 different prompts

---

## Follow-up Stories

- **E2E-005**: Error Handling & Validation
- **E2E-006**: Progress Reporting
- **Phase 3**: Timing Precision (±300ms accuracy)
