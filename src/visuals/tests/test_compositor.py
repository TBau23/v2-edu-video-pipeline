"""
Test video compositor (E2E-001).

Tests combining audio + video and stitching multiple videos.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.assembly.compositor import VideoCompositor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_combine():
    """Test combining audio + video"""
    logger.info("Test 1: Basic audio+video combine")

    compositor = VideoCompositor(Path("test_output/assembly"), quality="medium")

    # Use existing test files
    video = Path("test_output/composition/test_composition.mp4")
    audio = Path("test_output/audio/test_narration.mp3")

    if not video.exists():
        logger.error(f"✗ Video file not found: {video}")
        logger.info("  Run: cd src/visuals && python test_composition.py")
        return False

    if not audio.exists():
        logger.error(f"✗ Audio file not found: {audio}")
        return False

    try:
        output = compositor.combine_audio_video(
            video_path=video,
            audio_path=audio,
            output_path=Path("test_output/assembly/combined.mp4")
        )

        if output.exists():
            size_kb = output.stat().st_size // 1024
            duration = compositor.get_duration(output)
            logger.info(f"✓ Combined video created: {output}")
            logger.info(f"  Size: {size_kb}KB, Duration: {duration:.1f}s")
            return True
        else:
            logger.error("✗ Output file not created")
            return False

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_stitching():
    """Test stitching multiple videos together"""
    logger.info("\nTest 2: Video stitching")

    compositor = VideoCompositor(Path("test_output/assembly"), quality="medium")

    # Check if we have a combined video
    video1 = Path("test_output/assembly/combined.mp4")

    if not video1.exists():
        logger.info("  Skipping - no combined video available (run test 1 first)")
        return True  # Not a failure, just skip

    try:
        # For this test, we'll stitch the same video twice
        output = compositor.stitch_acts(
            videos=[video1, video1],
            output_path=Path("test_output/assembly/stitched.mp4")
        )

        if output.exists():
            size_kb = output.stat().st_size // 1024
            duration = compositor.get_duration(output)
            logger.info(f"✓ Stitched video created: {output}")
            logger.info(f"  Size: {size_kb}KB, Duration: {duration:.1f}s")

            # Duration should be roughly 2x the single video
            single_duration = compositor.get_duration(video1)
            expected_duration = single_duration * 2
            logger.info(f"  Expected ~{expected_duration:.1f}s (2x {single_duration:.1f}s)")

            return True
        else:
            logger.error("✗ Output file not created")
            return False

    except Exception as e:
        logger.error(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all compositor tests"""
    logger.info("=" * 60)
    logger.info("E2E-001: Video Compositor Tests")
    logger.info("=" * 60)

    results = []

    # Test 1: Basic combine
    results.append(("Basic audio+video combine", test_basic_combine()))

    # Test 2: Stitching
    results.append(("Video stitching", test_video_stitching()))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        logger.info("\n🎉 All tests passed!")
    else:
        logger.info("\n❌ Some tests failed")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
