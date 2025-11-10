"""
Example: Generate a video script using LLM.

This demonstrates the script generation pipeline:
1. Takes a user prompt
2. Calls OpenAI to generate a 5-act script with detailed visual specs
3. Creates a project workspace with the generated script
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(project_root / ".env")

from src.script.generator import generate_script
from src.utils.workspace import create_project


def main():
    """Generate a script for Newton's First Law."""

    # User prompt
    prompt = """
    Create an educational video explaining Newton's First Law of Motion.

    The video should:
    - Motivate the viewer with a relatable example
    - Explain the concept of inertia clearly
    - Show the mathematical formulation (F=ma, when F=0) and explain the components
    - Build up understanding of the physics
    - Conclude with real-world applications

    Keep it engaging and suitable for high school students.
    Target duration: 60-90 seconds.
    """

    print("Generating script from prompt...")
    print(f"Prompt: {prompt.strip()}\n")

    try:
        # Generate the script
        script = generate_script(prompt)

        print(f"✓ Script generated: {script.title}")
        print(f"  Topic: {script.topic}")
        print(f"  Acts: {script.act_count}")
        print(f"  Estimated duration: {script.estimated_total_duration:.1f}s\n")

        # Show each act
        for i, act in enumerate(script.acts, 1):
            print(f"Act {i}: {act.id}")
            print(f"  Purpose: {act.purpose}")
            print(f"  Duration: {act.estimated_duration}s")
            print(f"  Narration: {act.narration[:80]}...")
            print(f"  Visuals: {len(act.visuals)} visual(s)")
            for j, visual in enumerate(act.visuals, 1):
                print(f"    {j}. {visual.type}: {visual.content[:60]}...")
            print()

        # Create project workspace
        print("Creating project workspace...")
        workspace = create_project(script)

        print(f"✓ Project created: {workspace.project_id}")
        print(f"  Location: {workspace.root}")
        print(f"\nEditable files:")
        print(f"  - {workspace.script_file}")
        print(f"  - {workspace.style_file}")
        print("\nNext steps:")
        print("  1. Review and edit script.json if needed")
        print("  2. Generate audio from the script")
        print("  3. Render visuals with Manim")
        print("  4. Assemble final video")

    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo use script generation, set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("\nOr add it to your .env file:")
        print("  OPENAI_API_KEY=your-key-here")
        sys.exit(1)

    except Exception as e:
        print(f"Script generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
