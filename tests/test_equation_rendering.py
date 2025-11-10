"""
Test equation rendering with Manim.

Tests VIS-004 acceptance criteria:
- Basic equation rendering (F = ma)
- Animation styles (write, fade)
- Complex equations (fractions, summations)
- Style integration
- Positioning
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.primitives.models import Act, VisualSpec
from src.visuals.renderer import VisualRenderer
from src.style.config import StyleConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_equation():
    """Test basic equation rendering: F = ma"""
    logger.info("Test 1: Basic equation (F = ma)")

    style = StyleConfig.load_preset("default")
    output_dir = Path("test_output/equations")
    renderer = VisualRenderer(style, output_dir)

    act = Act(
        id="test_equation_basic",
        narration="F equals m a",
        visuals=[
            VisualSpec(
                type="equation",
                content="F = ma",
                animation_style="write",
                position="center",
                duration=2.0,
                params={"font_size": 48}
            )
        ],
        estimated_duration=3.0
    )

    result = renderer.render_act(act, target_duration=3.0)
    logger.info(f"✓ Rendered: {result.output_path}")

    if result.output_path.exists():
        logger.info(f"✓ File exists: {result.output_path.stat().st_size} bytes")
    else:
        logger.error(f"✗ File not found: {result.output_path}")
        return False

    return True


def test_animation_styles():
    """Test write and fade animations"""
    logger.info("Test 2: Animation styles (write vs fade)")

    style = StyleConfig.load_preset("default")
    output_dir = Path("test_output/equations")
    renderer = VisualRenderer(style, output_dir)

    # Test write animation
    act_write = Act(
        id="test_equation_write",
        narration="This equation writes",
        visuals=[
            VisualSpec(
                type="equation",
                content="E = mc^2",
                animation_style="write",
                position="center",
                duration=2.0,
                params={}
            )
        ],
        estimated_duration=3.0
    )

    result_write = renderer.render_act(act_write, target_duration=3.0)
    logger.info(f"✓ Write animation: {result_write.output_path}")

    # Test fade animation
    act_fade = Act(
        id="test_equation_fade",
        narration="This equation fades",
        visuals=[
            VisualSpec(
                type="equation",
                content="E = mc^2",
                animation_style="fade",
                position="center",
                duration=2.0,
                params={}
            )
        ],
        estimated_duration=3.0
    )

    result_fade = renderer.render_act(act_fade, target_duration=3.0)
    logger.info(f"✓ Fade animation: {result_fade.output_path}")

    return result_write.output_path.exists() and result_fade.output_path.exists()


def test_complex_equations():
    """Test complex LaTeX: fractions, summations, Greek letters"""
    logger.info("Test 3: Complex equations")

    style = StyleConfig.load_preset("default")
    output_dir = Path("test_output/equations")
    renderer = VisualRenderer(style, output_dir)

    test_cases = [
        ("fraction", r"\frac{F}{m} = a"),
        ("summation", r"\sum_{i=1}^{n} \frac{1}{i}"),
        ("greek", r"\alpha + \beta = \gamma"),
        ("integral", r"\int_{0}^{\infty} e^{-x} dx"),
    ]

    all_passed = True

    for name, latex in test_cases:
        act = Act(
            id=f"test_equation_{name}",
            narration=f"Test {name}",
            visuals=[
                VisualSpec(
                    type="equation",
                    content=latex,
                    animation_style="fade",
                    position="center",
                    duration=2.0,
                    params={}
                )
            ],
            estimated_duration=3.0
        )

        try:
            result = renderer.render_act(act, target_duration=3.0)
            logger.info(f"✓ {name}: {result.output_path}")

            if not result.output_path.exists():
                logger.error(f"✗ File not found: {result.output_path}")
                all_passed = False
        except Exception as e:
            logger.error(f"✗ {name} failed: {e}")
            all_passed = False

    return all_passed


def test_positioning():
    """Test positioning: center, top, bottom"""
    logger.info("Test 4: Positioning")

    style = StyleConfig.load_preset("default")
    output_dir = Path("test_output/equations")
    renderer = VisualRenderer(style, output_dir)

    positions = ["center", "top", "bottom"]
    all_passed = True

    for position in positions:
        act = Act(
            id=f"test_equation_pos_{position}",
            narration=f"Equation at {position}",
            visuals=[
                VisualSpec(
                    type="equation",
                    content="F = ma",
                    animation_style="fade",
                    position=position,
                    duration=2.0,
                    params={}
                )
            ],
            estimated_duration=3.0
        )

        try:
            result = renderer.render_act(act, target_duration=3.0)
            logger.info(f"✓ Position {position}: {result.output_path}")

            if not result.output_path.exists():
                logger.error(f"✗ File not found: {result.output_path}")
                all_passed = False
        except Exception as e:
            logger.error(f"✗ Position {position} failed: {e}")
            all_passed = False

    return all_passed


def main():
    """Run all equation rendering tests"""
    logger.info("=" * 60)
    logger.info("VIS-004: Equation Rendering Tests")
    logger.info("=" * 60)

    tests = [
        ("Basic equation", test_basic_equation),
        ("Animation styles", test_animation_styles),
        ("Complex equations", test_complex_equations),
        ("Positioning", test_positioning),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info("")
        logger.info(f"Running: {test_name}")
        logger.info("-" * 60)

        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        logger.info("")
        logger.info("🎉 All tests passed!")
    else:
        logger.info("")
        logger.info("❌ Some tests failed")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
