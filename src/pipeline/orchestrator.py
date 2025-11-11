"""
Video generation pipeline orchestrator.

Coordinates the full pipeline: prompt → script → audio → visuals → final video
"""

import logging
import hashlib
import sys
import time
import psutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from src.primitives.models import Script, AudioSegment
from src.script.generator import generate_script
from src.audio.synthesizer import AudioSynthesizer
from src.visuals.renderer import VisualRenderer
from src.assembly.compositor import VideoCompositor
from src.style.config import StyleConfig
from src.utils.io import save_pretty_json

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of full pipeline execution."""
    video_path: Path
    script: Script
    duration: float
    workspace: Path
    num_acts: int


class VideoPipeline:
    """Orchestrates end-to-end video generation from prompt."""

    def __init__(self, workspace_root: Path):
        """Initialize pipeline.

        Args:
            workspace_root: Root directory for all projects
        """
        self.workspace_root = workspace_root
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        prompt: str,
        project_id: Optional[str] = None,
        openai_key: Optional[str] = None,
        style_preset: str = "default"
    ) -> PipelineResult:
        """Run full pipeline: prompt → video.

        Args:
            prompt: Educational topic to explain
            project_id: Project ID (auto-generated if None)
            openai_key: OpenAI API key
            style_preset: Style preset name

        Returns:
            PipelineResult with video path and metadata

        Raises:
            RuntimeError: If any stage fails
        """
        # Setup
        if not project_id:
            project_id = self._generate_project_id(prompt)

        workspace = self._setup_workspace(project_id)

        logger.info("=" * 60)
        logger.info(f"Video Generation Pipeline: {project_id}")
        logger.info("=" * 60)
        logger.info(f"Prompt: {prompt}")
        logger.info(f"Workspace: {workspace}")

        # Log system resources
        try:
            mem = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            logger.info(f"System Resources:")
            logger.info(f"  CPU cores: {cpu_count}")
            logger.info(f"  RAM: {mem.total / (1024**3):.1f}GB total, {mem.available / (1024**3):.1f}GB available ({mem.percent}% used)")
        except Exception as e:
            logger.warning(f"Could not get system resources: {e}")

        logger.info("")
        sys.stdout.flush()

        start_time = time.time()

        try:
            # Stage 1: Generate script
            logger.info("🚀 Starting Stage 1/4: Script Generation")
            sys.stdout.flush()
            script = self._stage_script_generation(prompt, workspace, openai_key)

            # Stage 2: Synthesize audio
            logger.info("🚀 Starting Stage 2/4: Audio Synthesis")
            sys.stdout.flush()
            audio_segments = self._stage_audio_synthesis(script, workspace, openai_key)

            # Stage 3: Render visuals
            logger.info("🚀 Starting Stage 3/4: Visual Rendering (this may take a while)")
            sys.stdout.flush()
            visual_paths = self._stage_visual_rendering(
                script, audio_segments, workspace, style_preset, openai_key
            )

            # Stage 4: Assemble video
            logger.info("🚀 Starting Stage 4/4: Video Assembly")
            sys.stdout.flush()
            final_video = self._stage_video_assembly(
                audio_segments, visual_paths, workspace
            )

            # Calculate total duration
            total_duration = sum(audio.duration for audio in audio_segments)

            elapsed_time = time.time() - start_time

            logger.info("")
            logger.info("=" * 60)
            logger.info("✓ Pipeline complete!")
            logger.info(f"  Total processing time: {elapsed_time / 60:.1f} minutes")

            # Log final resource usage
            try:
                mem = psutil.virtual_memory()
                logger.info(f"  Final RAM usage: {mem.percent}% ({mem.available / (1024**3):.1f}GB available)")
            except Exception:
                pass

            logger.info("=" * 60)
            sys.stdout.flush()

            return PipelineResult(
                video_path=final_video,
                script=script,
                duration=total_duration,
                workspace=workspace,
                num_acts=len(script.acts)
            )

        except Exception as e:
            logger.error(f"✗ Pipeline failed: {e}", exc_info=True)
            sys.stdout.flush()
            raise RuntimeError(f"Pipeline failed at workspace: {workspace}") from e

    def _stage_script_generation(
        self,
        prompt: str,
        workspace: Path,
        openai_key: Optional[str]
    ) -> Script:
        """Stage 1: Generate script from prompt."""
        logger.info("[1/4] Generating script...")

        try:
            script = generate_script(
                user_prompt=prompt,
                api_key=openai_key
            )

            # Save to workspace
            script_path = workspace / "script.json"
            save_pretty_json(script.model_dump(), script_path)

            logger.info(f"  ✓ Script generated: {len(script.acts)} acts")
            logger.info(f"  ✓ Saved to: {script_path.name}")
            sys.stdout.flush()

            return script

        except Exception as e:
            logger.error(f"  ✗ Script generation failed: {e}", exc_info=True)
            sys.stdout.flush()
            raise RuntimeError("Script generation failed") from e

    def _stage_audio_synthesis(
        self,
        script: Script,
        workspace: Path,
        openai_key: Optional[str]
    ) -> list[AudioSegment]:
        """Stage 2: Synthesize audio for each Act."""
        logger.info("")
        logger.info("[2/4] Synthesizing audio...")

        audio_dir = workspace / "audio"
        audio_dir.mkdir(exist_ok=True)

        synthesizer = AudioSynthesizer(
            provider="openai",
            api_key=openai_key,
            cache_dir=workspace / ".audio_cache"
        )

        audio_segments = []

        for i, act in enumerate(script.acts, 1):
            logger.info(f"  [{i}/{len(script.acts)}] Act: {act.id}")

            try:
                audio_seg = synthesizer.synthesize_act(
                    act=act,
                    output_path=audio_dir / f"{act.id}.mp3"
                )

                audio_segments.append(audio_seg)
                logger.info(f"      ✓ {audio_seg.duration:.1f}s")
                sys.stdout.flush()

            except Exception as e:
                logger.error(f"      ✗ Failed: {e}", exc_info=True)
                sys.stdout.flush()
                raise RuntimeError(f"Audio synthesis failed for {act.id}") from e

        total_audio = sum(a.duration for a in audio_segments)
        logger.info(f"  ✓ Audio synthesized: {len(audio_segments)} files ({total_audio:.1f}s total)")
        sys.stdout.flush()

        return audio_segments

    def _stage_visual_rendering(
        self,
        script: Script,
        audio_segments: list[AudioSegment],
        workspace: Path,
        style_preset: str,
        openai_key: Optional[str]
    ) -> list[Path]:
        """Stage 3: Render visuals for each Act."""
        logger.info("")
        logger.info("[3/4] Rendering visuals...")

        visuals_dir = workspace / "visuals"
        visuals_dir.mkdir(exist_ok=True)

        # Use lower quality on resource-constrained environments (e.g., Render)
        import os
        render_quality = os.getenv("RENDER_QUALITY", "medium_quality")
        logger.info(f"  Using quality setting: {render_quality}")

        style = StyleConfig.load_preset(style_preset)
        renderer = VisualRenderer(
            style=style,
            output_dir=visuals_dir,
            quality=render_quality,
            openai_key=openai_key  # For LLM animation generation
        )

        visual_paths = []

        for i, (act, audio) in enumerate(zip(script.acts, audio_segments), 1):
            logger.info(f"  [{i}/{len(script.acts)}] Act: {act.id} - Starting render...")
            sys.stdout.flush()

            try:
                result = renderer.render_act(
                    act=act,
                    audio=audio  # Pass audio for timing sync
                )

                visual_paths.append(result.output_path)
                logger.info(f"      ✓ {result.output_path.name}")
                sys.stdout.flush()

            except Exception as e:
                logger.error(f"      ✗ Failed: {e}", exc_info=True)
                sys.stdout.flush()
                raise RuntimeError(f"Visual rendering failed for {act.id}") from e

        logger.info(f"  ✓ Visuals rendered: {len(visual_paths)} files")
        sys.stdout.flush()

        return visual_paths

    def _stage_video_assembly(
        self,
        audio_segments: list[AudioSegment],
        visual_paths: list[Path],
        workspace: Path
    ) -> Path:
        """Stage 4: Assemble final video."""
        logger.info("")
        logger.info("[4/4] Assembling final video...")

        assembly_dir = workspace / "assembly"
        assembly_dir.mkdir(exist_ok=True)

        compositor = VideoCompositor(assembly_dir, quality="medium")

        # Step 1: Combine audio + visuals for each Act
        logger.info("  Combining audio + visuals for each Act...")
        act_videos = []

        for i, (audio, visual) in enumerate(zip(audio_segments, visual_paths), 1):
            logger.info(f"    [{i}/{len(audio_segments)}] {audio.act_id}")
            sys.stdout.flush()

            try:
                act_video = compositor.combine_audio_video(
                    video_path=visual,
                    audio_path=audio.audio_path,
                    output_path=assembly_dir / f"{audio.act_id}.mp4"
                )
                act_videos.append(act_video)
                sys.stdout.flush()

            except Exception as e:
                logger.error(f"        ✗ Failed: {e}", exc_info=True)
                sys.stdout.flush()
                raise RuntimeError(f"Assembly failed for {audio.act_id}") from e

        # Step 2: Stitch all Acts together
        logger.info("  Stitching Acts together...")
        sys.stdout.flush()
        final_video = workspace / "final_video.mp4"

        try:
            compositor.stitch_acts(
                videos=act_videos,
                output_path=final_video
            )

            size_mb = final_video.stat().st_size / (1024 * 1024)
            logger.info(f"  ✓ Final video: {final_video.name} ({size_mb:.1f}MB)")
            sys.stdout.flush()

        except Exception as e:
            logger.error(f"  ✗ Stitching failed: {e}", exc_info=True)
            sys.stdout.flush()
            raise RuntimeError("Video stitching failed") from e

        return final_video

    def _generate_project_id(self, prompt: str) -> str:
        """Generate unique project ID from prompt."""
        # Use first few words
        words = prompt.lower().split()[:3]
        slug = "_".join(w for w in words if w.isalnum())

        # Add hash for uniqueness
        hash_short = hashlib.md5(prompt.encode()).hexdigest()[:6]

        # Add timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{slug}_{hash_short}_{timestamp}"

    def _setup_workspace(self, project_id: str) -> Path:
        """Create workspace directory structure."""
        workspace = self.workspace_root / project_id

        # Create subdirectories
        (workspace / "audio").mkdir(parents=True, exist_ok=True)
        (workspace / "visuals").mkdir(parents=True, exist_ok=True)
        (workspace / "assembly").mkdir(parents=True, exist_ok=True)

        logger.debug(f"Workspace created: {workspace}")

        return workspace
