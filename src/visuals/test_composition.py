"""
Quick test for multi-visual composition (VIS-008).
Tests rendering multiple visuals in one scene.
"""

from pathlib import Path
from manim import Scene, Text, FadeIn, Write, UP

from executor import SceneExecutor


class MultiTextScene(Scene):
    """Test scene with multiple text visuals"""

    def construct(self):
        # Visual 1: Title at top (2s)
        title = Text("Newton's First Law", font_size=48, color="#58a6ff")
        title.to_edge(UP)

        self.play(FadeIn(title), run_time=1.0)
        self.wait(1.0)

        # Visual 2: Description at center (3s)
        desc = Text("An object at rest stays at rest", font_size=32, color="#ffffff")
        # desc already centered by default

        self.play(Write(desc), run_time=2.0)
        self.wait(1.0)


def test_multi_visual():
    """Test multiple visuals in one scene"""
    print("Test: Multi-visual composition (title + description)")

    executor = SceneExecutor(Path("test_output/composition"), quality="low_quality")

    try:
        output = executor.render_scene(MultiTextScene, "test_composition", preview=True)
        print(f"✓ Multi-visual scene rendered: {output}")
        print(f"✓ File size: {output.stat().st_size} bytes")
        return True
    except Exception as e:
        print(f"✗ Composition test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("VIS-008: Multi-Visual Composition Test")
    print("=" * 60)

    success = test_multi_visual()

    print("\n" + "=" * 60)
    if success:
        print("✓ Composition test passed!")
        exit(0)
    else:
        print("✗ Composition test failed")
        exit(1)
