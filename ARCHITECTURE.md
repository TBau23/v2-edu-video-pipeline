# Architecture Specification

## Problem Statement

Generate high-quality educational videos programmatically from a single text prompt, with:
- Consistent style across videos
- Precise audio-visual synchronization (±300ms)
- Easy iteration on individual components without breaking the pipeline
- Production-quality animations that actually teach concepts

**Core Challenge**: The hardest problems are not script generation (LLMs can do this), but:
1. Creating **meaningful animations** that explain concepts clearly
2. **Timing synchronization** between narration and visuals
3. Making the system **modular and editable** for iteration

## Design Principles

### 1. Composability Over Monoliths
- System is built from small, independent primitives
- Each primitive has a clear responsibility
- Primitives compose into larger structures (Acts → Scripts → Projects)

### 2. Editability as a First-Class Concern
- All intermediate outputs are human-readable JSON
- Users can edit any layer and regenerate downstream
- No "black box" processing - everything is inspectable

### 3. Timing-First Architecture
- Timing is not an afterthought - it's built into every primitive
- Audio synthesis produces word-level timestamps
- Visual specs include duration hints
- Synchronization happens at assembly time with metadata from all layers

### 4. Declarative Over Imperative
- Visual specs describe WHAT to show, not HOW to render
- Rendering engine interprets specs (allows swapping renderers)
- Style is data (JSON), not code

## Core Primitives

All primitives are Pydantic models for type safety and JSON serialization.

### VisualSpec
**Purpose**: Declarative description of a visual element

```python
VisualSpec(
    type="equation" | "graph" | "animation" | "diagram" | "text",
    content="detailed description or LaTeX",
    animation_style="draw" | "fade" | "write" | "play",
    position="center" | "top" | "bottom" | "left" | "right",
    duration=2.0,  # seconds, optional
    params={...}   # type-specific parameters
)
```

**Key Insight**: Must be detailed enough to actually render, not vague placeholders.

### Act
**Purpose**: Single video segment (the atomic unit of iteration)

```python
Act(
    id="act_1_motivation",
    narration="Spoken text...",
    visuals=[VisualSpec, ...],
    estimated_duration=12.0,
    purpose="What this accomplishes",
    notes="Internal iteration notes"
)
```

**Key Insight**: Acts are independent - you can regenerate one without affecting others.

### Script
**Purpose**: Complete video structure (collection of Acts)

```python
Script(
    title="Video Title",
    topic="Brief description",
    acts=[Act, Act, ...],
    source_prompt="Original user prompt",
    style_profile="default"
)
```

**Structure**: Scripts follow a flexible pedagogical pattern (typically 3-7 acts):
- Motivation/Intro (hook with real-world scenario)
- Concept explanation (high-level understanding)
- Equation/Formula (mathematical representation)
- Examples (build intuition through concrete cases)
- Conclusion/Applications

The exact number of acts adapts to content complexity. Not every video needs exactly 5 acts.

### AudioSegment
**Purpose**: Generated audio with precise timing metadata

```python
AudioSegment(
    act_id="act_1_motivation",
    audio_path=Path("..."),
    duration=12.5,
    word_timestamps=[
        {"word": "Imagine", "start": 0.0, "end": 0.4},
        ...
    ],
    provider="openai",
    voice_id="alloy"
)
```

**Key Insight**: Word-level timestamps enable precise synchronization.

### StyleConfig
**Purpose**: Consistent visual/audio styling across videos

```python
StyleConfig(
    colors=ColorPalette(...),
    typography=Typography(...),
    animation=AnimationTiming(...),
    voice=VoiceConfig(...),
    layout=LayoutConfig(...)
)
```

**Key Insight**: Style is data, stored as JSON, versioned with projects.

### VideoProject
**Purpose**: Top-level container for all project artifacts

```python
VideoProject(
    project_id="unique_id",
    script=Script,
    audio_segments=[AudioSegment, ...],
    workspace_path=Path("projects/project_id/"),
    status="script_only" | "audio_generated" | "visuals_generated" | "assembled"
)
```

## Pipeline Architecture

```
┌─────────────┐
│ User Prompt │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ 1. Script Generator │  (LLM)
│                     │
│ Input:  Prompt      │
│ Output: Script JSON │
│                     │
│ • Generates 5 acts  │
│ • Detailed visuals  │
│ • Timing estimates  │
└──────┬──────────────┘
       │
       ▼  (User can edit script.json here)
┌─────────────────────┐
│ 2. Audio Synthesis  │  (TTS)
│                     │
│ Input:  Script acts │
│ Output: Audio files │
│         + timestamps│
│                     │
│ • Per-act audio     │
│ • Word-level timing │
│ • Natural pauses    │
└──────┬──────────────┘
       │
       ▼  (Actual durations now known)
┌─────────────────────┐
│ 3. Visual Renderer  │  (Manim)
│                     │
│ Input:  VisualSpecs │
│         + timing    │
│ Output: Animations  │
│                     │
│ • Parse specs       │
│ • Generate scenes   │
│ • Render to video   │
└──────┬──────────────┘
       │
       ▼  (All assets ready)
┌─────────────────────┐
│ 4. Video Assembly   │  (ffmpeg)
│                     │
│ Input:  Audio files │
│         Visual files│
│         Sync metadata│
│ Output: Final MP4   │
│                     │
│ • Align audio/video │
│ • Composite layers  │
│ • Preview/final     │
└──────┬──────────────┘
       │
       ▼
┌─────────────┐
│  Final MP4  │
└─────────────┘
```

### Layer Independence

Each layer:
- Has clear input/output contracts (Pydantic models)
- Can be run independently
- Outputs editable artifacts (JSON)
- Can be re-run without affecting upstream

**Iteration Example**:
1. Generate script → Get `script.json`
2. Edit act 3's narration manually
3. Regenerate audio for act 3 only
4. Visuals and other acts unchanged
5. Re-assemble video

## Project Workspace Structure

```
projects/
  {project_name}_{timestamp}/

    # Editable artifacts (user can modify)
    project.json       # VideoProject metadata
    script.json        # Script with acts (EDIT THIS)
    style.json         # StyleConfig (EDIT THIS)

    # Generated assets (regenerate if inputs change)
    audio/
      act_1_motivation.mp3
      act_2_concept.mp3
      ...

    visuals/
      act_1_motivation_visual_0.mp4
      act_2_concept_visual_0.mp4
      ...

    renders/
      preview.mp4      # Low-res for fast iteration
      final.mp4        # High-res final output

    metadata/
      sync.json        # Timing alignment metadata
      audio_timing.json
```

## Module Organization

```
src/
  primitives/
    models.py         # Core Pydantic models
    __init__.py

  script/
    generator.py      # LLM-based script generation
    __init__.py

  audio/
    synthesizer.py    # TTS integration (OpenAI, ElevenLabs)
    timing.py         # Word-level timestamp extraction
    __init__.py

  visuals/
    renderer.py       # VisualSpec → Manim Scene
    scenes.py         # Manim scene definitions
    parsers.py        # Parse VisualSpec params
    __init__.py

  assembly/
    compositor.py     # Video assembly with ffmpeg
    sync.py           # Audio-visual synchronization
    __init__.py

  style/
    config.py         # StyleConfig models
    presets/          # Style presets as JSON
      default.json
      light.json
      dark.json

  utils/
    io.py             # File I/O (save/load JSON)
    workspace.py      # Project workspace management
    __init__.py
```

## Data Flow

### 1. Script Generation
```
User Prompt
  → LLM (with detailed system prompt)
  → Script JSON
  → Save to workspace/script.json
```

**Critical**: LLM prompt teaches:
- 5-act structure
- How to write detailed VisualSpecs (not vague)
- Timing guidelines (150 words/min, visual lead time)
- Examples of good vs bad specs

### 2. Audio Synthesis
```
Script.acts[i].narration
  → TTS API (OpenAI/ElevenLabs)
  → Audio file (.mp3)
  → Word timestamps (from API or forced alignment)
  → AudioSegment model
  → Save to workspace/audio/
```

**Critical**: Must extract word-level timestamps for sync.

### 3. Visual Rendering
```
Act.visuals[j] (VisualSpec)
  → Parse params
  → Generate Manim Scene code
  → Render scene (manim render)
  → Video file (.mp4, no audio)
  → Save to workspace/visuals/
```

**Critical**:
- Parser must handle all VisualSpec types
- Timing must match duration hints
- Output must be compositable

### 4. Assembly
```
AudioSegments + Visual files + Sync metadata
  → Calculate precise alignment (word timestamps → visual cues)
  → ffmpeg composition:
      - Audio track
      - Video track (stitch visuals with timing)
      - Overlays (equations, text)
  → Output: preview.mp4 or final.mp4
```

**Critical**: Target ±300ms synchronization accuracy.

## Key Technical Decisions

### 1. Why Pydantic Models?
- Type safety catches errors early
- JSON serialization built-in
- Validation ensures data correctness
- Documentation via types

### 2. Why JSON for Intermediate Artifacts?
- Human-readable (essential for iteration)
- Easy to version control
- Can be edited manually
- Language-agnostic

### 3. Why 5-Act Structure?
- Pedagogically proven (motivation → concept → math → examples → conclusion)
- Clear structure for LLM to follow
- Natural breakpoints for iteration

### 4. Why Separate Audio and Visual Rendering?
- Audio timing must be known before visual rendering
- TTS is slow - don't block on it
- Can regenerate visuals without re-synthesizing audio
- Parallelizable (can render multiple acts' visuals concurrently)

### 5. Why Manim?
- Best-in-class for mathematical animations
- Programmatic (can generate scenes from specs)
- LaTeX support built-in
- High-quality output

## Iteration Workflows

### Workflow 1: Tweak Narration
1. Edit `script.json` → change Act 3 narration
2. Run audio synthesis for Act 3 only
3. Re-assemble video (other acts unchanged)

### Workflow 2: Improve Visual
1. Edit `script.json` → change Act 2 visual params
2. Re-render Act 2 visuals only
3. Re-assemble video (audio unchanged)

### Workflow 3: Change Style
1. Edit `style.json` → change colors
2. Re-render all visuals (audio unchanged)
3. Re-assemble video

### Workflow 4: Regenerate from LLM
1. Run script generator with different prompt
2. Review generated `script.json`
3. Edit as needed
4. Continue pipeline

## Synchronization Strategy

**Goal**: Visuals appear at the right moment in narration (±300ms accuracy)

### Approach
1. **Audio-first**: Generate audio to get true durations
2. **Word timestamps**: Extract from TTS API or forced alignment
3. **Visual cues**: Mark when each visual should appear
   ```json
   {
     "visual_id": "act_2_equation_0",
     "trigger_word": "mathematically",
     "trigger_time": 5.3,
     "duration": 2.0
   }
   ```
4. **Assembly**: ffmpeg timeline with precise timing
   ```
   [audio] ─────────────────────────
   [visual1]  ████────────────────
   [visual2]  ─────████───────────
   [visual3]  ──────────████──────
   ```

### Timing Hints in VisualSpec
```python
VisualSpec(
    ...,
    timing_hint="before_narration" | "during_narration" | "after_narration",
    trigger_words=["mathematically", "equation"],
    duration=2.0
)
```

Renderer uses these hints + word timestamps to calculate exact appearance time.

## Success Criteria

From `project_high_level_outline.md`:

1. ✅ Single prompt input
2. ✅ 5-act structure with narration and visuals
3. 🔲 Audio-visual sync within ±300ms
4. 🔲 Deterministic re-runs (same input → similar output)
5. ✅ Iteration without breaking existing work (JSON editing)
6. 🔲 Style consistency (fonts, colors, pacing, voice)
7. 🔲 Final output: 1080p MP4, 80-180s duration

## What's Built vs. What's Needed

### ✅ Completed
- Core primitives (models)
- Workspace management
- Style configuration system
- Script generation (LLM with detailed prompts)
- Project structure

### 🔲 TODO
- **Audio synthesis** (TTS + word timestamps) - CRITICAL
- **Visual rendering** (VisualSpec → Manim scenes) - CRITICAL
- **Synchronization** (align audio + visuals) - CRITICAL
- **Assembly** (ffmpeg composition)
- Preview mode (low-res iteration)
- Web UI (for non-technical users)

## Next Steps

**Priority 1: Visual Rendering**
- Build VisualSpec parser
- Create Manim scene generators for each type
- Handle timing/duration accurately

**Priority 2: Audio Synthesis**
- Integrate OpenAI TTS
- Extract word-level timestamps
- Add natural pauses

**Priority 3: Synchronization & Assembly**
- Calculate alignment from timestamps
- ffmpeg composition with precise timing
- Validation (check sync accuracy)

---

**Key Philosophy**:
Animation quality and timing precision are harder than script generation. The architecture prioritizes these by:
1. Making visual specs detailed and actionable
2. Building timing into every primitive
3. Keeping layers independent for iteration
4. Using declarative specs that can be refined without code changes
