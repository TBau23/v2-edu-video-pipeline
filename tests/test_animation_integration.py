"""
Test animation integration with VisualSpecs.

Tests that animations from AnimationLibrary can be rendered
through the VisualSpec → Renderer pipeline.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.primitives.models import Act, VisualSpec
from src.style.config import StyleConfig
from src.visuals.renderer import VisualRenderer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_car_accelerating():
    """Test car_accelerating animation."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing car_accelerating animation")
    logger.info("=" * 60)

    # Create VisualSpec for car animation
    visual = VisualSpec(
        type="animation",
        content="car_accelerating",
        animation_style="play",
        duration=4.0,
        position="center",
        params={
            "start_pos": [-4, 0, 0],
            "end_pos": [4, 0, 0],
            "acceleration": 1.5,
            "show_motion_lines": True
        }
    )

    # Create Act with this visual
    act = Act(
        id="test_car",
        narration="A car accelerates from left to right",
        visuals=[visual],
        estimated_duration=4.0
    )

    # Setup renderer
    output_dir = Path("test_output/animation_tests")
    style = StyleConfig.load_preset("default")
    renderer = VisualRenderer(style, output_dir, quality="low_quality")

    try:
        # Render
        result = renderer.render_act(act, target_duration=4.0)

        # Verify
        if result.output_path.exists():
            size_mb = result.output_path.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Animation rendered successfully")
            logger.info(f"  Output: {result.output_path}")
            logger.info(f"  Size: {size_mb:.2f} MB")
            logger.info(f"  Duration: {result.duration:.1f}s")
            return True
        else:
            logger.error("✗ Output file not created")
            return False

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hockey_puck_sliding():
    """Test hockey_puck_sliding animation."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing hockey_puck_sliding animation")
    logger.info("=" * 60)

    # Create VisualSpec for hockey puck
    visual = VisualSpec(
        type="animation",
        content="hockey_puck_sliding",
        animation_style="play",
        duration=3.0,
        position="center",
        params={
            "start_pos": [-4, 0, 0],
            "end_pos": [4, 0, 0],
            "velocity": 2.0,
            "show_motion_lines": True
        }
    )

    # Create Act
    act = Act(
        id="test_hockey_puck",
        narration="A hockey puck slides at constant velocity",
        visuals=[visual],
        estimated_duration=3.0
    )

    # Setup renderer
    output_dir = Path("test_output/animation_tests")
    style = StyleConfig.load_preset("default")
    renderer = VisualRenderer(style, output_dir, quality="low_quality")

    try:
        # Render
        result = renderer.render_act(act, target_duration=3.0)

        # Verify
        if result.output_path.exists():
            size_mb = result.output_path.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Animation rendered successfully")
            logger.info(f"  Output: {result.output_path}")
            logger.info(f"  Size: {size_mb:.2f} MB")
            logger.info(f"  Duration: {result.duration:.1f}s")
            return True
        else:
            logger.error("✗ Output file not created")
            return False

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_object_at_rest():
    """Test object_at_rest animation."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing object_at_rest animation")
    logger.info("=" * 60)

    # Create VisualSpec for object at rest
    visual = VisualSpec(
        type="animation",
        content="object_at_rest",
        animation_style="play",
        duration=2.0,
        position="center",
        params={
            "obj_type": "book",
            "show_forces": True
        }
    )

    # Create Act
    act = Act(
        id="test_object_rest",
        narration="A book at rest with force arrows",
        visuals=[visual],
        estimated_duration=2.0
    )

    # Setup renderer
    output_dir = Path("test_output/animation_tests")
    style = StyleConfig.load_preset("default")
    renderer = VisualRenderer(style, output_dir, quality="low_quality")

    try:
        # Render
        result = renderer.render_act(act, target_duration=2.0)

        # Verify
        if result.output_path.exists():
            size_mb = result.output_path.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Animation rendered successfully")
            logger.info(f"  Output: {result.output_path}")
            logger.info(f"  Size: {size_mb:.2f} MB")
            logger.info(f"  Duration: {result.duration:.1f}s")
            return True
        else:
            logger.error("✗ Output file not created")
            return False

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all animation integration tests."""
    logger.info("\n" + "=" * 60)
    logger.info("Animation Integration Tests")
    logger.info("=" * 60)

    results = []

    # Run tests
    results.append(("car_accelerating", test_car_accelerating()))
    results.append(("hockey_puck_sliding", test_hockey_puck_sliding()))
    results.append(("object_at_rest", test_object_at_rest()))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("\n✓ All tests passed!")
        return 0
    else:
        logger.error("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
