# Educational Video Generation Pipeline

A modular, composable pipeline for generating high-quality educational videos using AI and Manim.

## Architecture

**Design Philosophy**: Modular pipeline with composable primitives, emphasizing editability and iteration.

### Core Primitives

All primitives are Pydantic models that serialize to/from JSON for easy editing:

- **Act**: Fundamental unit representing one video segment (narration + visuals + timing)
- **Script**: Collection of Acts with metadata (5-act pedagogical structure)
- **VisualSpec**: Declarative description of what to show (equation, graph, animation, diagram, text)
- **AudioSegment**: Generated audio with timing metadata for sync
- **VideoProject**: Top-level project container with all artifacts

### Pipeline Layers

```
User Prompt → Script Generation → Audio Synthesis → Visual Generation → Video Assembly
                     ↓                  ↓                  ↓                  ↓
                [5 Acts]          [Audio + Timing]    [Manim Renders]    [Final MP4]
```

1. **Script Generation**: LLM generates complete 5-act structure with detailed narration and visual specs
2. **Audio Synthesis**: TTS (OpenAI/ElevenLabs) generates audio with word-level timestamps
3. **Visual Generation**: Manim renders animations, equations, graphs based on VisualSpecs
4. **Assembly**: ffmpeg combines audio + visuals with precise synchronization

## Project Structure

```
src/
  primitives/      # Core data models (Act, Script, VisualSpec, etc.)
  script/          # LLM-based script generation
  audio/           # TTS integration (TODO)
  visuals/         # Manim scene generation (TODO)
  assembly/        # Video compilation (TODO)
  style/           # Style system (colors, fonts, timing, voice)
  utils/           # File I/O and workspace management

projects/          # User project workspaces
  project_name_YYYY_MM_DD/
    project.json   # VideoProject metadata
    script.json    # Editable script
    style.json     # Editable style config
    audio/         # Generated audio files
    visuals/       # Generated animations
    renders/       # Final videos
```

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set OpenAI API key (for script generation and TTS):
```bash
export OPENAI_API_KEY='your-key-here'
# Or add to .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
```

## Usage

### Generate a Script

```bash
source venv/bin/activate
python examples/generate_script.py
```

This will:
1. Use LLM to generate a 5-act script with detailed narration and visual specs
2. Create a project workspace with editable JSON files
3. Output: `projects/*/script.json` (ready to edit and iterate)

### Create a Project Manually

```bash
python examples/create_simple_project.py
```

Creates a project with hardcoded Acts (useful for testing).

## Key Features

### 1. Editability
All outputs are human-readable JSON:
- Edit `script.json` to tweak narration or visual descriptions
- Edit `style.json` to change colors, fonts, timing
- Regenerate from any point in the pipeline

### 2. Modularity
Each layer is independent:
- Swap TTS providers (OpenAI ↔ ElevenLabs)
- Change visual rendering engine
- Iterate on script without regenerating audio

### 3. Timing-Aware
Built for precise audio-visual sync:
- Word-level timestamps from TTS
- Visual timing hints in VisualSpecs
- Target: ±300ms synchronization

### 4. Pedagogically Sound
5-act structure proven effective:
1. Motivation (hook with real-world example)
2. Concept (high-level explanation)
3. Equation (mathematical formulation)
4. Examples (3 concrete cases)
5. Conclusion (applications and summary)

## Roadmap

- [x] Core primitives and data models
- [x] Workspace management system
- [x] Style configuration system
- [x] Script generation with LLM
- [ ] Audio synthesis (OpenAI TTS + ElevenLabs)
- [ ] Visual rendering with Manim
- [ ] Audio-visual synchronization
- [ ] Video assembly with ffmpeg
- [ ] Preview mode (low-res fast iteration)
- [ ] Web UI for prompts and iteration

## Contributing

See `project_high_level_outline.md` for detailed requirements and success criteria.

## License

[TBD]
