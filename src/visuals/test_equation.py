"""
Quick test for equation rendering (VIS-004).
Tests that we can render LaTeX equations with Manim.
"""

from pathlib import Path
from manim import Scene, MathTex, Write, FadeIn

from executor import SceneExecutor


class EquationTestScene(Scene):
    """Test scene with F = ma equation"""

    def construct(self):
        # Create equation
        equation = MathTex(
            "F = ma",
            color="#58a6ff",
            font_size=48
        )

        # Animate with Write
        self.play(Write(equation), run_time=2.0)
        self.wait(1)


class ComplexEquationTestScene(Scene):
    """Test scene with complex equation"""

    def construct(self):
        # Test fraction
        equation = MathTex(
            r"\frac{F}{m} = a",
            color="#58a6ff",
            font_size=48
        )

        self.play(FadeIn(equation), run_time=1.5)
        self.wait(1)


def test_basic_equation():
    """Test basic equation rendering"""
    print("Test 1: Basic equation (F = ma)")

    executor = SceneExecutor(Path("test_output/equations"), quality="low_quality")

    try:
        output = executor.render_scene(EquationTestScene, "test_equation_basic", preview=True)
        print(f"✓ Basic equation rendered: {output}")
        return True
    except Exception as e:
        print(f"✗ Basic equation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complex_equation():
    """Test complex equation rendering"""
    print("\nTest 2: Complex equation (fraction)")

    executor = SceneExecutor(Path("test_output/equations"), quality="low_quality")

    try:
        output = executor.render_scene(ComplexEquationTestScene, "test_equation_fraction", preview=True)
        print(f"✓ Complex equation rendered: {output}")
        return True
    except Exception as e:
        print(f"✗ Complex equation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("VIS-004: Equation Rendering Test")
    print("=" * 60)

    test1 = test_basic_equation()
    test2 = test_complex_equation()

    print("\n" + "=" * 60)
    if test1 and test2:
        print("✓ All equation tests passed!")
        exit(0)
    else:
        print("✗ Some tests failed")
        exit(1)
