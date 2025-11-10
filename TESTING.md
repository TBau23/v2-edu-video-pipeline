# Testing Guide

How to test each component of the educational video generation pipeline.

## Prerequisites

1. **Virtual environment activated**:
```bash
source venv/bin/activate
```

2. **API keys set** (if testing with LLM/TTS):
```bash
export OPENAI_API_KEY="your-key-here"
# Or add to .env file:
echo "OPENAI_API_KEY=your-key-here" >> .env
```

## Test 1: Core Primitives

Verify that the basic data models work:

```bash
python examples/create_simple_project.py
```

**Expected output**:
```
Creating project for: Newton's First Law of Motion
Total estimated duration: 60.0 seconds
Number of acts: 5

Project created at: /path/to/projects/inertia_and_constant_velocity_TIMESTAMP

Generated files:
  - project.json (project metadata)
  - script.json (editable script)
  - style.json (editable style config)
```

**Verify**:
- Check that `projects/` directory was created
- Open `script.json` - should be readable JSON with 5 acts
- Open `style.json` - should have colors, typography, voice settings

## Test 2: Script Generation (Requires OpenAI API Key)

Generate a script using LLM:

```bash
python examples/generate_script.py
```

**Expected output**:
```
Generating script from prompt...

✓ Script generated: Newton's First Law of Motion
  Topic: inertia and constant velocity
  Acts: 5
  Estimated duration: 60.0s

Act 1: act_1_motivation
  Purpose: Hook the viewer
  Duration: 12s
  Narration: Imagine you're in a car...
  Visuals: 1 visual(s)
    1. animation: A simple car accelerating...

...

✓ Project created: project_id
  Location: /path/to/projects/project_id

Next steps:
  1. Review and edit script.json if needed
  2. Generate audio from the script
  3. Render visuals with Manim
  4. Assemble final video
```

**Verify**:
- Check that VisualSpecs are detailed (not vague like "car_animation")
- Look for proper LaTeX in equation visuals (`F = ma`, not placeholder text)
- Verify timing estimates are reasonable
- Edit `script.json` to tweak narration or visuals

**If it fails**:
- Check API key is set: `echo $OPENAI_API_KEY`
- Check internet connection
- Check OpenAI API status

## Test 3: Audio Synthesis (Requires OpenAI API Key)

Generate audio for a script:

```bash
python examples/generate_audio.py
```

**Expected output**:
```
Available projects:
  1. project_id_1
  2. project_id_2

Using project: project_id_2

Script: Newton's First Law of Motion
Acts: 5
Estimated duration: 60.0s

Initializing audio synthesizer...

Synthesizing audio...

Synthesizing audio for act_1_motivation...
  ✓ Duration: 12.34s
Synthesizing audio for act_2_concept...
  ✓ Duration: 10.56s
...

Audio generation complete!

act_1_motivation:
  Duration: 12.34s
  Audio: /path/to/projects/project_id/audio/act_1_motivation.mp3
  Words: 45 timestamps

Total duration: 62.3s

Audio files saved to: /path/to/audio/
Timing metadata: /path/to/metadata/audio_timing.json
```

**Verify**:
- Audio files exist in `workspace/audio/`
- Listen to audio files (should sound natural)
- Check `metadata/audio_timing.json` - should have duration data
- Run again - should be instant (cached)

**Check timing accuracy**:
```bash
# Play an audio file (macOS)
afplay projects/*/audio/act_1_motivation.mp3

# Check duration
ffprobe -i projects/*/audio/act_1_motivation.mp3 -show_entries format=duration -v quiet -of csv="p=0"
```

**If it fails**:
- Check API key is set
- Check you have disk space for audio files
- Check pydub is installed (for duration extraction)

## Test 4: Visual Rendering (Manim)

Test that Manim can render scenes:

```bash
python src/visuals/executor.py
```

This runs a simple test: renders a circle animation.

**Expected output**:
```
Test render successful: test_output/test_circle.mp4
```

**If it fails**:
- Manim may not be properly installed
- Check LaTeX is installed (required by Manim for equations)
  - macOS: `brew install --cask mactex`
  - Linux: `sudo apt-get install texlive-full`
- Check FFmpeg is installed
  - `brew install ffmpeg` (macOS)
  - `sudo apt-get install ffmpeg` (Linux)

## Test 5: Full Integration Test

Create a test script that runs the entire pipeline:

```bash
python tests/test_integration.py
```

(We'll create this next)

## Manual Testing Workflow

### 1. Generate Script
```bash
python examples/generate_script.py
```

### 2. Review and Edit Script
```bash
# Find the latest project
ls -lt projects/ | head -2

# Edit the script
code projects/YOUR_PROJECT_ID/script.json
# or
nano projects/YOUR_PROJECT_ID/script.json
```

Edit narration, visual descriptions, timing, etc.

### 3. Generate Audio
```bash
python examples/generate_audio.py
```

### 4. Listen to Audio
```bash
# List audio files
ls projects/YOUR_PROJECT_ID/audio/

# Play them
afplay projects/YOUR_PROJECT_ID/audio/act_1_motivation.mp3
afplay projects/YOUR_PROJECT_ID/audio/act_2_concept.mp3
```

### 5. Check Timing
```bash
# View timing metadata
cat projects/YOUR_PROJECT_ID/metadata/audio_timing.json | python -m json.tool
```

### 6. Render Visuals (TODO)
```bash
python examples/render_visuals.py
```

### 7. Assemble Video (TODO)
```bash
python examples/assemble_video.py
```

## Debugging Common Issues

### "Module not found" errors
```bash
# Make sure you're in the right directory
pwd  # should show .../v2-education-vid-gen

# Make sure venv is activated
which python  # should show .../venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

### "API key not found"
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Set it
export OPENAI_API_KEY="sk-..."

# Or use .env file
echo "OPENAI_API_KEY=sk-..." >> .env
```

### "Permission denied" errors
```bash
# Make sure scripts are executable
chmod +x examples/*.py

# Or run with python explicitly
python examples/generate_script.py
```

### Manim rendering fails
```bash
# Test Manim independently
manim --version

# Simple Manim test
echo "from manim import *
class TestScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
        self.wait(1)" > test_scene.py

manim -ql test_scene.py TestScene
```

## Performance Testing

### Script Generation Speed
```bash
time python examples/generate_script.py
# Should take: 5-15 seconds (depends on LLM)
```

### Audio Synthesis Speed
```bash
time python examples/generate_audio.py
# First run: ~10-30 seconds (5 acts × 2-6s each)
# Cached run: <1 second
```

### Visual Rendering Speed (TODO)
```bash
time python examples/render_visuals.py
# Expected: 1-5 minutes per act (depends on complexity)
```

## Test Checklist

Before considering a component "working":

**Script Generation**:
- [ ] Generates 3-7 acts with proper structure
- [ ] VisualSpecs are detailed and actionable
- [ ] Equations use valid LaTeX
- [ ] Timing estimates are reasonable
- [ ] Output is valid JSON

**Audio Synthesis**:
- [ ] Audio files are generated
- [ ] Audio sounds natural (not robotic)
- [ ] Duration matches narration length
- [ ] Caching works (2nd run is instant)
- [ ] Timing metadata is saved

**Visual Rendering**:
- [ ] Equations render correctly
- [ ] Text appears with proper styling
- [ ] Animations execute
- [ ] Timing matches specified duration
- [ ] Output is valid MP4

**Assembly**:
- [ ] Audio and video are synchronized
- [ ] Multiple visuals composite correctly
- [ ] Sync is within ±300ms
- [ ] Final video plays smoothly
- [ ] Output is 1080p MP4

## Next Steps

Once basic tests pass:
1. Test with different topics (not just Newton's Laws)
2. Test edge cases (very short/long narration, complex equations)
3. Measure sync accuracy (±300ms target)
4. Profile performance (identify bottlenecks)
5. Add automated tests (pytest)
