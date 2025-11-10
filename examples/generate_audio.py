"""
Example: Generate audio for a script.

This demonstrates the audio synthesis pipeline:
1. Load a script from a project
2. Synthesize audio for all Acts
3. Save AudioSegments with timing data to workspace
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.audio.synthesizer import AudioSynthesizer
from src.utils.workspace import load_project, list_projects
from src.utils.io import save_json
from src.style.config import StyleConfig


def main():
    """Generate audio for an existing project."""

    # List available projects
    projects = list_projects()

    if not projects:
        print("No projects found. Create a project first using generate_script.py")
        return

    print("Available projects:")
    for i, project_id in enumerate(projects, 1):
        print(f"  {i}. {project_id}")

    # Use the most recent project (last in list)
    project_id = projects[-1]
    print(f"\nUsing project: {project_id}\n")

    # Load project
    workspace = load_project(project_id)
    script = workspace.load_script()
    style = workspace.load_style()

    print(f"Script: {script.title}")
    print(f"Acts: {script.act_count}")
    print(f"Estimated duration: {script.estimated_total_duration:.1f}s\n")

    # Initialize audio synthesizer
    print("Initializing audio synthesizer...")
    synthesizer = AudioSynthesizer(
        provider="openai",  # or "elevenlabs"
        style=style
    )

    # Synthesize audio for all acts
    print("\nSynthesizing audio...\n")
    try:
        audio_segments = synthesizer.synthesize_script(
            script=script,
            output_dir=workspace.audio_dir,
            use_cache=True  # Use cache to avoid regenerating
        )

        # Update project with audio segments
        project = workspace.load_project()
        project.audio_segments = audio_segments
        project.status = "audio_generated"
        workspace.save_project(project)

        # Save timing metadata
        timing_data = {
            "acts": [
                {
                    "act_id": seg.act_id,
                    "duration": seg.duration,
                    "word_count": len(seg.word_timestamps) if seg.word_timestamps else 0,
                    "has_timestamps": seg.word_timestamps is not None
                }
                for seg in audio_segments
            ],
            "total_duration": sum(seg.duration for seg in audio_segments)
        }

        save_json(timing_data, workspace.metadata_dir / "audio_timing.json")

        # Summary
        print("\n" + "="*60)
        print("Audio generation complete!")
        print("="*60)

        for seg in audio_segments:
            print(f"\n{seg.act_id}:")
            print(f"  Duration: {seg.duration:.2f}s")
            print(f"  Audio: {seg.audio_path}")
            if seg.word_timestamps:
                print(f"  Words: {len(seg.word_timestamps)} timestamps")
            else:
                print(f"  Words: No timestamps (estimated)")

        total_duration = sum(seg.duration for seg in audio_segments)
        print(f"\nTotal duration: {total_duration:.1f}s")
        print(f"\nAudio files saved to: {workspace.audio_dir}")
        print(f"Timing metadata: {workspace.metadata_dir / 'audio_timing.json'}")

        print("\nNext steps:")
        print("  1. Review audio files")
        print("  2. Edit script.json if narration needs changes")
        print("  3. Re-run to regenerate specific acts")
        print("  4. Generate visuals with timing data")

    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo use audio synthesis, set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nOr add it to your .env file:")
        print("  OPENAI_API_KEY=your-key-here")
        sys.exit(1)

    except Exception as e:
        print(f"Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
