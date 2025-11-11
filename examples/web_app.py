"""
Educational Video Generator - Web Interface (Gradio)

Simple web app for generating educational videos from prompts.
Designed for deployment to Hugging Face Spaces (free hosting).

Usage:
    Local: python examples/web_app.py
    Deployed: Auto-runs on Hugging Face Spaces
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import gradio as gr
from src.pipeline.orchestrator import VideoPipeline


def generate_video(prompt: str) -> str:
    """Generate educational video from prompt.

    Args:
        prompt: Educational topic to explain

    Returns:
        Path to generated video file
    """
    if not prompt or len(prompt.strip()) < 10:
        raise gr.Error("Please enter a more detailed prompt (at least 10 characters)")

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise gr.Error("OPENAI_API_KEY not configured. Please contact the administrator.")

    try:
        # Initialize pipeline
        workspace = project_root / "projects"
        pipeline = VideoPipeline(workspace)

        # Generate video
        result = pipeline.generate(
            prompt=prompt,
            openai_key=api_key
        )

        return str(result.video_path)

    except Exception as e:
        print(f"Error generating video: {e}")
        import traceback
        traceback.print_exc()
        raise gr.Error(f"Video generation failed: {str(e)}")


# Create Gradio interface
demo = gr.Interface(
    fn=generate_video,
    inputs=gr.Textbox(
        label="📚 Educational Topic",
        placeholder="Example: Explain Newton's First Law with a car accelerating",
        lines=4
    ),
    outputs=gr.Video(
        label="",
        autoplay=True
    ),
    title="🎓 AI Educational Video Generator",
    description="""
    Enter an educational topic and get an AI-generated explanation video with narration,
    equations, and animations.

    **⏱️ Note**: Generation takes 3-5 minutes. Please be patient!
    """,
    cache_examples=False,
    flagging_mode="never",
    theme=gr.themes.Soft()
)


if __name__ == "__main__":
    # Enable queue for long-running tasks
    demo.queue(max_size=3)  # Allow up to 3 queued requests

    # Launch server
    demo.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,        # Standard Gradio port
        share=False              # HF Spaces handles sharing
    )
