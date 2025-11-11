---
title: Educational Video Generator
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🎓 AI Educational Video Generator

Generate educational videos from text prompts using AI. Enter a topic, wait 3-5 minutes, and get a complete video with narration, equations, and animations.

## How it works

1. **Enter a topic**: Describe what concept you want explained
2. **AI generates**:
   - Script with structured acts
   - Natural-sounding narration (text-to-speech)
   - Mathematical equations and diagrams
   - Physics animations
3. **Get video**: Watch or download the final MP4

## Example Prompts

- "Explain Newton's First Law with a car accelerating on a highway"
- "What is the Pythagorean theorem? Show it with a right triangle"
- "Describe photosynthesis with diagrams of a plant cell"
- "Explain momentum using a hockey puck sliding on ice"

## Tech Stack

- **Script Generation**: OpenAI GPT-4
- **Audio Synthesis**: OpenAI TTS
- **Visual Rendering**: Manim (mathematics animation engine)
- **Video Assembly**: FFmpeg

## ⏱️ Note on Speed

Video generation takes **3-5 minutes** (or 5-10 minutes on free tier hardware). This is because:
- AI generates a detailed script
- Text-to-speech creates narration
- Manim renders equations and animations
- FFmpeg assembles everything into final video

Please be patient! The result is worth the wait.

## Tips for Best Results

- **Be specific**: "Explain photosynthesis with a chloroplast diagram" is better than just "photosynthesis"
- **Include examples**: "Use a car example for acceleration" helps the AI understand what you want
- **One concept per video**: Focus on a single topic rather than multiple concepts
- **Mention visual preferences**: If you want equations, animations, or diagrams, say so!

## Credits

Built with:
- [Manim](https://www.manim.community/) - Mathematics animation engine
- [Gradio](https://gradio.app/) - Web interface
- [OpenAI](https://openai.com/) - GPT-4 and TTS
- [FFmpeg](https://ffmpeg.org/) - Video processing

## Source Code

View the full source code and documentation at: [GitHub Repository Link]

## Limitations

- Public free hosting (videos may take longer to generate)
- Single user at a time (others queue automatically)
- Videos deleted after 24 hours (download to keep)
- English language only
- Topics limited to physics, math, and basic sciences

## Support

Having issues? Check the logs or contact the developer.
