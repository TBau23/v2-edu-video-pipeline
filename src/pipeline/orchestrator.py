"""
Video generation pipeline orchestrator.

Coordinates the full pipeline: prompt → script → audio → visuals → final video
"""

import logging
import hashlib
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
        logger.info("")

        try:
            # Stage 1: Generate script
            script = self._stage_script_generation(prompt, workspace, openai_key)

            # Stage 2: Synthesize audio
            audio_segments = self._stage_audio_synthesis(script, workspace, openai_key)

            # Stage 3: Render visuals
            visual_paths = self._stage_visual_rendering(
                script, audio_segments, workspace, style_preset
            )

            # Stage 4: Assemble video
            final_video = self._stage_video_assembly(
                audio_segments, visual_paths, workspace
            )

            # Calculate total duration
            total_duration = sum(audio.duration for audio in audio_segments)

            logger.info("")
            logger.info("=" * 60)
            logger.info("✓ Pipeline complete!")
            logger.info("=" * 60)

            return PipelineResult(
                video_path=final_video,
                script=script,
                duration=total_duration,
                workspace=workspace,
                num_acts=len(script.acts)
            )

        except Exception as e:
            logger.error(f"✗ Pipeline failed: {e}")
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

            return script

        except Exception as e:
            logger.error(f"  ✗ Script generation failed: {e}")
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

            except Exception as e:
                logger.error(f"      ✗ Failed: {e}")
                raise RuntimeError(f"Audio synthesis failed for {act.id}") from e

        total_audio = sum(a.duration for a in audio_segments)
        logger.info(f"  ✓ Audio synthesized: {len(audio_segments)} files ({total_audio:.1f}s total)")

        return audio_segments

    def _stage_visual_rendering(
        self,
        script: Script,
        audio_segments: list[AudioSegment],
        workspace: Path,
        style_preset: str
    ) -> list[Path]:
        """Stage 3: Render visuals for each Act."""
        logger.info("")
        logger.info("[3/4] Rendering visuals...")

        visuals_dir = workspace / "visuals"
        visuals_dir.mkdir(exist_ok=True)

        style = StyleConfig.load_preset(style_preset)
        renderer = VisualRenderer(
            style=style,
            output_dir=visuals_dir,
            quality="medium_quality"  # Can be configurable later
        )

        visual_paths = []

        for i, (act, audio) in enumerate(zip(script.acts, audio_segments), 1):
            logger.info(f"  [{i}/{len(script.acts)}] Act: {act.id}")

            try:
                result = renderer.render_act(
                    act=act,
                    audio=audio  # Pass audio for timing sync
                )

                visual_paths.append(result.output_path)
                logger.info(f"      ✓ {result.output_path.name}")

            except Exception as e:
                logger.error(f"      ✗ Failed: {e}")
                raise RuntimeError(f"Visual rendering failed for {act.id}") from e

        logger.info(f"  ✓ Visuals rendered: {len(visual_paths)} files")

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

            try:
                act_video = compositor.combine_audio_video(
                    video_path=visual,
                    audio_path=audio.audio_path,
                    output_path=assembly_dir / f"{audio.act_id}.mp4"
                )
                act_videos.append(act_video)

            except Exception as e:
                logger.error(f"        ✗ Failed: {e}")
                raise RuntimeError(f"Assembly failed for {audio.act_id}") from e

        # Step 2: Stitch all Acts together
        logger.info("  Stitching Acts together...")
        final_video = workspace / "final_video.mp4"

        try:
            compositor.stitch_acts(
                videos=act_videos,
                output_path=final_video
            )

            size_mb = final_video.stat().st_size / (1024 * 1024)
            logger.info(f"  ✓ Final video: {final_video.name} ({size_mb:.1f}MB)")

        except Exception as e:
            logger.error(f"  ✗ Stitching failed: {e}")
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
