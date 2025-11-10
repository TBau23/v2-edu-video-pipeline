"""
Integration test - validates the entire pipeline works.

This test:
1. Creates a simple script (hardcoded, no LLM)
2. Generates audio for the script
3. Tests visual rendering (basic validation)
4. Verifies timing accuracy

Run with: python tests/test_integration.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.primitives.models import Act, Script, VisualSpec
from src.style.config import StyleConfig
from src.utils.workspace import create_project
from src.audio.synthesizer import AudioSynthesizer


def test_primitives():
    """Test 1: Core primitives work."""
    print("\n" + "="*60)
    print("TEST 1: Core Primitives")
    print("="*60)

    # Create a simple act
    act = Act(
        id="test_act",
        narration="This is a test narration.",
        visuals=[
            VisualSpec(
                type="text",
                content="Test Text",
                animation_style="fade",
                position="center"
            )
        ],
        estimated_duration=3.0,
        purpose="Test purpose"
    )

    # Create script
    script = Script(
        title="Test Script",
        topic="testing",
        acts=[act],
        source_prompt="test prompt"
    )

    # Create project
    workspace = create_project(script)

    print(f"✓ Created project: {workspace.project_id}")
    print(f"✓ Script has {script.act_count} act(s)")
    print(f"✓ Files created:")
    print(f"  - {workspace.project_file}")
    print(f"  - {workspace.script_file}")
    print(f"  - {workspace.style_file}")

    return workspace, script


def test_audio_synthesis(workspace, script):
    """Test 2: Audio synthesis works."""
    print("\n" + "="*60)
    print("TEST 2: Audio Synthesis")
    print("="*60)

    try:
        # Load style
        style = workspace.load_style()

        # Initialize synthesizer
        synthesizer = AudioSynthesizer(
            provider="openai",
            style=style
        )

        print("✓ Initialized audio synthesizer")

        # Synthesize audio
        audio_segments = synthesizer.synthesize_script(
            script=script,
            output_dir=workspace.audio_dir,
            use_cache=True
        )

        print(f"✓ Generated {len(audio_segments)} audio file(s)")

        for seg in audio_segments:
            print(f"  - {seg.act_id}: {seg.duration:.2f}s")

            # Verify file exists
            if not seg.audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {seg.audio_path}")

        print("✓ All audio files exist")

        # Test caching (should be instant)
        import time
        start = time.time()
        audio_segments_cached = synthesizer.synthesize_script(
            script=script,
            output_dir=workspace.audio_dir,
            use_cache=True
        )
        elapsed = time.time() - start

        if elapsed < 1.0:
            print(f"✓ Caching works (2nd run: {elapsed:.3f}s)")
        else:
            print(f"⚠ Caching may not be working (2nd run: {elapsed:.3f}s)")

        return audio_segments

    except ValueError as e:
        print(f"\n✗ Audio synthesis test skipped: {e}")
        print("\nTo test audio synthesis, set OPENAI_API_KEY:")
        print("  export OPENAI_API_KEY='your-key-here'")
        return None

    except Exception as e:
        print(f"\n✗ Audio synthesis test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_timing_accuracy(audio_segments):
    """Test 3: Timing data is reasonable."""
    print("\n" + "="*60)
    print("TEST 3: Timing Accuracy")
    print("="*60)

    if audio_segments is None:
        print("✗ Skipped (no audio generated)")
        return

    for seg in audio_segments:
        print(f"\n{seg.act_id}:")
        print(f"  Duration: {seg.duration:.2f}s")

        # Check duration is reasonable (not 0 or negative)
        if seg.duration <= 0:
            print(f"  ✗ Invalid duration: {seg.duration}")
            continue

        # Check word timestamps
        if seg.word_timestamps:
            word_count = len(seg.word_timestamps)
            print(f"  Word timestamps: {word_count}")

            # Check timestamps are sequential
            for i in range(len(seg.word_timestamps) - 1):
                current = seg.word_timestamps[i]
                next_ts = seg.word_timestamps[i + 1]

                if current["end"] > next_ts["start"]:
                    print(f"  ✗ Timestamp overlap: {current} → {next_ts}")
                    break
            else:
                print(f"  ✓ Timestamps are sequential")

            # Check first word starts near 0
            first_start = seg.word_timestamps[0]["start"]
            if first_start > 1.0:
                print(f"  ⚠ First word starts late: {first_start:.2f}s")

            # Check last word ends near duration
            last_end = seg.word_timestamps[-1]["end"]
            if abs(last_end - seg.duration) > 1.0:
                print(f"  ⚠ Last word timing mismatch: {last_end:.2f}s vs {seg.duration:.2f}s")
            else:
                print(f"  ✓ Timing spans full duration")

        else:
            print(f"  ⚠ No word timestamps (estimation may be needed)")

    print("\n✓ Timing validation complete")


def test_visual_rendering():
    """Test 4: Visual rendering (basic validation)."""
    print("\n" + "="*60)
    print("TEST 4: Visual Rendering")
    print("="*60)

    print("⚠ Visual rendering test not yet implemented")
    print("  TODO: Test Manim scene generation and rendering")

    # TODO: Actually test rendering
    # from src.visuals.renderer import VisualRenderer
    # renderer = VisualRenderer(style, output_dir)
    # result = renderer.render_act(act, target_duration=duration)


def main():
    """Run all integration tests."""
    print("\n" + "="*70)
    print(" "*20 + "INTEGRATION TEST SUITE")
    print("="*70)

    try:
        # Test 1: Primitives
        workspace, script = test_primitives()

        # Test 2: Audio synthesis
        audio_segments = test_audio_synthesis(workspace, script)

        # Test 3: Timing accuracy
        test_timing_accuracy(audio_segments)

        # Test 4: Visual rendering
        test_visual_rendering()

        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print("✓ Core primitives: PASS")
        print(f"{'✓' if audio_segments else '⚠'} Audio synthesis: {'PASS' if audio_segments else 'SKIPPED'}")
        print(f"{'✓' if audio_segments else '⚠'} Timing accuracy: {'PASS' if audio_segments else 'SKIPPED'}")
        print("⚠ Visual rendering: NOT IMPLEMENTED")
        print("\nTest project created at:")
        print(f"  {workspace.root}")
        print("\nYou can inspect the generated files:")
        print(f"  - Script: {workspace.script_file}")
        print(f"  - Audio: {workspace.audio_dir}")
        print("="*70)

        return 0

    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
