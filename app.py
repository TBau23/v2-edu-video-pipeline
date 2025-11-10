"""
Hugging Face Spaces entry point for Educational Video Generator.

This file is required by HF Spaces - it imports and launches the Gradio app.
The actual app logic is in examples/web_app.py
"""

from examples.web_app import demo

# Launch the Gradio interface
# HF Spaces handles the server configuration automatically
demo.launch()
