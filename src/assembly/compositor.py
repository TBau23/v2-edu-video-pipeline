"""
Video compositor - assembles final video from audio and visual components.

Uses ffmpeg for:
- Combining audio + video
- Concatenating multiple videos
- Duration alignment
- Quality settings
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Quality presets
QUALITY_PRESETS = {
    "low": {
        "resolution": (854, 480),
        "video_bitrate": "1M",
        "crf": 28,
        "preset": "fast",
        "audio_bitrate": "96k"
    },
    "medium": {
        "resolution": (1280, 720),
        "video_bitrate": "2.5M",
        "crf": 23,
        "preset": "medium",
        "audio_bitrate": "128k"
    },
    "high": {
        "resolution": (1920, 1080),
        "video_bitrate": "5M",
        "crf": 20,
        "preset": "slow",
        "audio_bitrate": "192k"
    }
}


@dataclass
class CompositionResult:
    """Result of video composition."""
    output_path: Path
    duration: float
    file_size: int


class VideoCompositor:
    """Assembles final video from audio + visual components using ffmpeg."""

    def __init__(self, output_dir: Path, quality: str = "medium"):
        """Initialize compositor.

        Args:
            output_dir: Directory for output videos
            quality: Quality preset ('low', 'medium', 'high')
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quality = quality

        if quality not in QUALITY_PRESETS:
            raise ValueError(f"Invalid quality: {quality}. Choose from: {list(QUALITY_PRESETS.keys())}")

        self.quality_settings = QUALITY_PRESETS[quality]

    def combine_audio_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        resolution: Optional[tuple] = None
    ) -> Path:
        """Combine single video + audio into MP4.

        Args:
            video_path: Path to video file (.mp4)
            audio_path: Path to audio file (.mp3 or .wav)
            output_path: Where to save combined video
            resolution: Override resolution (width, height)

        Returns:
            Path to output video

        Raises:
            FileNotFoundError: If input files don't exist
            RuntimeError: If ffmpeg fails
        """
        # Validate inputs
        self._validate_input_files(video_path, audio_path)

        # Get quality settings
        width, height = resolution or self.quality_settings["resolution"]
        crf = self.quality_settings["crf"]
        preset = self.quality_settings["preset"]
        audio_bitrate = self.quality_settings["audio_bitrate"]

        logger.info(f"Combining {video_path.name} + {audio_path.name}")
        logger.debug(f"Quality: {self.quality} ({width}x{height}, crf={crf})")

        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-loglevel", "warning",
            "-i", str(video_path),
            "-i", str(audio_path),
            # Video settings
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-vf", f"scale={width}:{height}",
            # Audio settings
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            # Stream mapping
            "-map", "0:v:0",  # Video from first input
            "-map", "1:a:0",  # Audio from second input
            # Output
            str(output_path)
        ]

        # Run ffmpeg
        self._run_ffmpeg(cmd)

        logger.info(f"✓ Combined: {output_path.name} ({output_path.stat().st_size // 1024}KB)")

        return output_path

    def stitch_acts(
        self,
        videos: List[Path],
        output_path: Path
    ) -> Path:
        """Concatenate multiple videos sequentially.

        Args:
            videos: List of video file paths (in order)
            output_path: Where to save stitched video

        Returns:
            Path to output video

        Raises:
            ValueError: If videos list is empty
            RuntimeError: If ffmpeg fails
        """
        if not videos:
            raise ValueError("No videos to stitch")

        logger.info(f"Stitching {len(videos)} videos...")

        # Create concat file (ffmpeg requires this format)
        concat_file = self.output_dir / "concat_list.txt"

        with open(concat_file, "w") as f:
            for video in videos:
                if not video.exists():
                    raise FileNotFoundError(f"Video not found: {video}")
                # ffmpeg concat format requires file paths
                f.write(f"file '{video.absolute()}'\n")

        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "warning",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",  # Copy streams without re-encoding (fast)
            str(output_path)
        ]

        # Run ffmpeg
        self._run_ffmpeg(cmd)

        # Clean up concat file
        concat_file.unlink()

        logger.info(f"✓ Stitched: {output_path.name} ({output_path.stat().st_size // 1024}KB)")

        return output_path

    def get_duration(self, file_path: Path) -> float:
        """Get media file duration using ffprobe.

        Args:
            file_path: Path to media file

        Returns:
            Duration in seconds
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        return float(result.stdout.strip())

    def _validate_input_files(self, *files: Path):
        """Validate input files exist and are non-empty."""
        for file_path in files:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if file_path.stat().st_size == 0:
                raise ValueError(f"File is empty: {file_path}")

    def _run_ffmpeg(self, cmd: List[str], timeout: int = 300):
        """Run ffmpeg command with error handling.

        Args:
            cmd: ffmpeg command arguments
            timeout: Timeout in seconds

        Raises:
            RuntimeError: If ffmpeg fails or times out
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=timeout
            )

            # Log any warnings
            if result.stderr:
                logger.debug(f"ffmpeg stderr: {result.stderr}")

        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed (exit code {e.returncode})")
            logger.error(f"stderr: {e.stderr}")
            raise RuntimeError(f"ffmpeg failed: {e.stderr}") from e

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"ffmpeg timed out after {timeout}s")
