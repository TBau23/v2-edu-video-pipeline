"""
Scene executor - runs Manim rendering programmatically.

This module handles the actual invocation of Manim's rendering system
to convert Scene classes into video files.
"""

import tempfile
import subprocess
from pathlib import Path
from typing import Type, Optional

from manim import Scene, config as manim_config


class SceneExecutor:
    """Executes Manim scene rendering."""

    def __init__(self, output_dir: Path, quality="medium_quality"):
        """Initialize executor.

        Args:
            output_dir: Directory for output videos
            quality: Render quality ('low_quality', 'medium_quality', 'high_quality')
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.quality = quality

    def render_scene(
        self,
        scene_class: Type[Scene],
        output_name: str,
        preview=False
    ) -> Path:
        """Render a Manim scene to a video file.

        Args:
            scene_class: Scene class to render
            output_name: Output filename (without extension)
            preview: If True, render low quality for fast iteration

        Returns:
            Path to the rendered video file

        Note:
            Manim's programmatic API is tricky. There are two approaches:
            1. Use manim.config and render directly (what we'll try first)
            2. Write scene to temp .py file and invoke `manim` CLI

            We'll implement approach #1 for cleaner integration.
        """
        # Configure quality
        quality_flag = "l" if preview else "m"
        if self.quality == "high_quality":
            quality_flag = "h"

        # Set output path
        output_file = self.output_dir / f"{output_name}.mp4"

        # Configure Manim
        manim_config.output_file = output_name
        manim_config.media_dir = str(self.output_dir / "media")
        manim_config.video_dir = str(self.output_dir)

        if preview:
            manim_config.quality = "low_quality"
            manim_config.preview = False
        elif self.quality == "high_quality":
            manim_config.quality = "high_quality"
        else:
            manim_config.quality = "medium_quality"

        # Render the scene
        try:
            scene = scene_class()
            scene.render()

            # Find the output file (Manim puts it in a specific location)
            # This is simplified - real version needs to find Manim's output
            return output_file

        except Exception as e:
            print(f"Rendering failed: {e}")
            raise

    def render_scene_via_cli(
        self,
        scene_class: Type[Scene],
        output_name: str,
        preview=False
    ) -> Path:
        """Alternative: render via CLI by writing temp file.

        This is more robust but less elegant. Useful as fallback.

        Args:
            scene_class: Scene class to render
            output_name: Output filename
            preview: If True, use low quality

        Returns:
            Path to rendered video
        """
        # Create temp Python file with scene
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir=self.output_dir
        ) as f:
            # Write scene code to file
            f.write("from manim import *\n\n")
            f.write(f"class TempScene(Scene):\n")
            f.write(f"    def construct(self):\n")
            # TODO: Serialize scene construction code
            # This is complex - need to convert Scene object back to code

            temp_file = Path(f.name)

        # Run manim CLI
        quality_flag = "-ql" if preview else "-qm"
        if self.quality == "high_quality":
            quality_flag = "-qh"

        cmd = [
            "manim",
            quality_flag,
            str(temp_file),
            "TempScene",
            "-o",
            output_name,
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.output_dir,
                capture_output=True,
                text=True,
                check=True
            )

            # Clean up temp file
            temp_file.unlink()

            # Return path to output
            return self.output_dir / f"{output_name}.mp4"

        except subprocess.CalledProcessError as e:
            print(f"Manim CLI failed: {e.stderr}")
            raise

        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()


def render_simple_test():
    """Test function to verify Manim rendering works."""

    class TestScene(Scene):
        def construct(self):
            from manim import Circle, Create
            circle = Circle()
            self.play(Create(circle))
            self.wait(1)

    executor = SceneExecutor(Path("test_output"), quality="low_quality")

    try:
        output = executor.render_scene(TestScene, "test_circle", preview=True)
        print(f"Test render successful: {output}")
        return True
    except Exception as e:
        print(f"Test render failed: {e}")
        return False


if __name__ == "__main__":
    # Run test
    success = render_simple_test()
    exit(0 if success else 1)
