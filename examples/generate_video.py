"""
Generate educational video from text prompt.

This is the main entry point for the video generation pipeline.

Usage:
    python examples/generate_video.py --prompt "Explain Newton's First Law"

Options:
    --prompt TEXT       Educational topic to explain (required)
    --project-id TEXT   Project ID (auto-generated if not provided)
    --output PATH       Output directory (default: projects)
    --style TEXT        Style preset (default: default)

Example:
    python examples/generate_video.py \
        --prompt "Explain F=ma using a car accelerating" \
        --project-id newtons_second_law
"""

import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.orchestrator import VideoPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate educational video from prompt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--prompt",
        required=True,
        help="Educational topic to explain"
    )
    parser.add_argument(
        "--project-id",
        help="Project ID (default: auto-generated from prompt)"
    )
    parser.add_argument(
        "--output",
        default="projects",
        help="Output directory (default: projects)"
    )
    parser.add_argument(
        "--style",
        default="default",
        help="Style preset (default: default)"
    )

    args = parser.parse_args()

    # Load environment
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(env_path)
    else:
        logger.warning(f".env file not found at {env_path}")

    # Get API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("Error: OPENAI_API_KEY not found")
        logger.error("Please set it in .env file or environment")
        return 1

    # Run pipeline
    try:
        pipeline = VideoPipeline(Path(args.output))

        result = pipeline.generate(
            prompt=args.prompt,
            project_id=args.project_id,
            openai_key=openai_key,
            style_preset=args.style
        )

        # Print results
        print("\n" + "=" * 60)
        print("✓ Video generation complete!")
        print("=" * 60)
        print(f"Video:     {result.video_path}")
        print(f"Duration:  {result.duration:.1f}s")
        print(f"Acts:      {result.num_acts}")
        print(f"Workspace: {result.workspace}")
        print("=" * 60)
        print(f"\nTo play: open {result.video_path}")
        print("")

        return 0

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130

    except Exception as e:
        logger.error(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
