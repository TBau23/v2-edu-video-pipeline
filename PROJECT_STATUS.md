# Project Status - Educational Video Generation Pipeline

## What We've Built

### ✅ Core Architecture (100% Complete)

**Primitives** (`src/primitives/models.py`)
- Pydantic models for all data structures
- `VisualSpec`: Declarative visual descriptions (equation, text, graph, animation, diagram)
- `Act`: Single video segment (narration + visuals + timing)
- `Script`: Collection of Acts (flexible structure, typically 3-7 acts)
- `AudioSegment`: Audio file + word-level timestamps
- `VideoProject`: Top-level container with status tracking

**Why Pydantic**: Type safety, JSON serialization, validation, documentation

**Workspace System** (`src/utils/`)
- Project folder structure: `projects/{id}/{script.json, audio/, visuals/, renders/}`
- All artifacts are human-readable JSON (editable for iteration)
- Save/load utilities for all primitives
- Status tracking (script_only → audio_generated → visuals_generated → assembled)

**Why this matters**: Users can edit `script.json`, regenerate downstream, and nothing breaks

### ✅ Script Generation (100% Complete)

**What**: LLM converts user prompt → detailed Script with Acts
**How**: OpenAI GPT-4 with comprehensive system prompt
**Location**: `src/script/generator.py`

**Key Achievement**: System prompt teaches LLM to generate **actionable** VisualSpecs
- Not vague: ~~"car_animation"~~
- Specific: "A simple car (rectangle with wheels) accelerating from left to right with motion lines"
- Includes parameters: velocity, direction, colors, duration

**Why this matters**: Renderer can actually generate animations from the specs

**Flexible Structure**: Not locked to 5 acts - adapts to content (3-7 acts typical)

### ✅ Audio Synthesis (100% Complete)

**What**: Converts Act narration → audio files with timing data
**Location**: `src/audio/`

**Components**:
1. **Provider abstraction** (`providers.py`)
   - OpenAI TTS (implemented)
   - ElevenLabs TTS (ready)
   - Unified interface

2. **Timing extraction** (`timing.py`)
   - Word-level timestamp estimation (±500ms accuracy)
   - Accounts for punctuation pauses
   - TODO: Forced alignment for ±50ms accuracy

3. **Audio synthesizer** (`synthesizer.py`)
   - Caching system (hash-based, avoids regenerating unchanged audio)
   - StyleConfig integration (voice, speed, pauses)
   - Workspace integration

**Why caching matters**: Iteration is instant for unchanged acts (no API calls, no wait)

**Current limitation**: Timestamp estimation is good enough for prototyping but forced alignment needed for production (±300ms sync target)

### ✅ Style System (100% Complete)

**What**: Centralized styling configuration
**Location**: `src/style/config.py`

**Covers**:
- Colors (background, primary, accent, equation colors)
- Typography (font family, sizes for different elements)
- Animation timing (fade duration, pauses, easing)
- Voice config (provider, voice ID, speed, pause markers)
- Layout (resolution, FPS, margins)

**Stored as JSON**: `style.json` in each project (user-editable)

**Why this matters**: Consistent look across videos, easy to create themes

### ⚠️ Visual Rendering (Architecture Complete, Implementation 60%)

**What**: VisualSpec → Manim Scene → rendered video
**Location**: `src/visuals/`

**What's Built**:
1. **Renderer architecture** (`renderer.py`)
   - Parses VisualSpecs and generates Manim Scene classes
   - Handles 5 visual types (equation, text, graph, animation, diagram)
   - Composes multiple visuals per Act
   - Timing-aware (uses audio duration)

2. **Animation library** (`animations.py`)
   - Reusable physics animations (car_accelerating, hockey_puck_sliding, etc.)
   - Math animations (equation_progressive_reveal, function_plot_animated)
   - Registry system (look up by name)

3. **Scene executor** (`executor.py`)
   - Programmatic Manim rendering
   - Quality settings (low/medium/high for preview vs final)

**What's Not Tested**:
- Actual Manim rendering (code exists, needs validation)
- Graph function plotting (axes work, function drawing TODO)
- Animation parameter parsing (spec params → Manim args)
- Diagram rendering (force diagrams, labeled illustrations)

**Why this is hard**: Creating meaningful animations that teach concepts, not just graphics

## What's Missing

### ❌ Video Assembly (0% Complete)

**What**: Combine audio + visuals → final MP4
**Location**: `src/assembly/` (doesn't exist yet)

**Needs**:
1. **Compositor** - ffmpeg integration
   - Stitch visuals with proper timing
   - Add audio track
   - Composite multiple visual layers
   - Handle transitions

2. **Synchronization** - align audio + visuals
   - Use word timestamps to trigger visual cues
   - Target: ±300ms accuracy
   - Validation/measurement

3. **Quality modes**:
   - Preview: low-res, fast (for iteration)
   - Final: 1080p, 30fps

### ❌ End-to-End Testing (0% Complete)

- Need to validate: prompt → script → audio → visuals → final video
- Need to measure sync accuracy
- Need to test iteration workflows

### ❌ Polish & UX (0% Complete)

- Progress indicators
- Error recovery
- Batch processing (multiple videos)
- Web UI (future)

## Key Design Decisions & Why

### 1. Modular Pipeline Over Monolith
**Decision**: Each layer (script, audio, visuals, assembly) is independent
**Why**: Can iterate on one without breaking others. Edit `script.json` → regenerate audio for one act → done.

### 2. JSON Artifacts Over Database
**Decision**: All intermediate outputs are JSON files
**Why**: Human-readable, easy to version control, easy to edit manually

### 3. Timing-First Architecture
**Decision**: Timing built into every primitive
**Why**: Audio-visual sync is the hardest technical problem. Can't be an afterthought.

### 4. Animation Library Over Generation
**Decision**: Curate reusable animations instead of generating from scratch
**Why**: Quality control. LLM references `car_accelerating` with params, not generating code.

### 5. Estimation + Forced Alignment Strategy
**Decision**: Start with timestamp estimation, add forced alignment later
**Why**: Estimation (±500ms) good enough for prototyping. Forced alignment (±50ms) for production.

## Architecture in One Diagram

```
User Prompt
    ↓
┌─────────────────────┐
│ Script Generator    │ ✅ DONE
│ (LLM)               │
└──────┬──────────────┘
       │ script.json (editable)
       ↓
┌─────────────────────┐
│ Audio Synthesizer   │ ✅ DONE
│ (TTS + Timing)      │
└──────┬──────────────┘
       │ audio/*.mp3 + timestamps
       ↓
┌─────────────────────┐
│ Visual Renderer     │ ⚠️ 60% DONE (needs testing)
│ (Manim)             │
└──────┬──────────────┘
       │ visuals/*.mp4
       ↓
┌─────────────────────┐
│ Video Assembly      │ ❌ TODO
│ (ffmpeg)            │
└──────┬──────────────┘
       │
       ▼
   final.mp4
```

## Current Capabilities

**What works today**:
1. ✅ Prompt → detailed script with actionable visuals
2. ✅ Script → audio files with timing data
3. ✅ Caching system for fast iteration
4. ✅ Workspace management (all artifacts organized)
5. ✅ JSON editing workflow (edit script, regenerate audio)

**What doesn't work yet**:
1. ❌ Actually rendering Manim scenes (code exists, untested)
2. ❌ Synchronizing audio + visuals into final video
3. ❌ End-to-end: prompt → final MP4

## Technical Debt & Known Issues

1. **Timestamp accuracy**: Using estimation (±500ms). Need forced alignment for ±300ms target.
2. **Graph rendering**: Axes render, but function plotting incomplete.
3. **Animation params**: Mapping VisualSpec params to Manim animation args needs work.
4. **Manim executor**: Programmatic rendering approach needs validation.
5. **Error handling**: Limited error recovery throughout pipeline.
6. **Performance**: No profiling or optimization yet.

## What You Can Test Right Now

```bash
# 1. Generate a script (needs OPENAI_API_KEY)
python examples/generate_script.py

# 2. Generate audio for that script
python examples/generate_audio.py

# 3. Listen to audio
afplay projects/*/audio/act_1_motivation.mp3

# 4. Edit script.json manually
code projects/*/script.json

# 5. Regenerate audio (instant if cached)
python examples/generate_audio.py
```

## Success Criteria (from original requirements)

1. ✅ Single prompt input
2. ✅ Modular structure with narration and visuals
3. ❌ Audio-visual sync within ±300ms (not yet testable)
4. ⚠️ Deterministic re-runs (mostly, depends on LLM temp=0.7)
5. ✅ Iteration without breaking work (JSON editing works)
6. ✅ Style consistency system (StyleConfig)
7. ❌ Final output: 1080p MP4, 80-180s (assembly not built)

**Score: 4/7 complete, 1/7 partial**

## Bottom Line

**What's strong**: Architecture, primitives, script generation, audio synthesis, editability
**What's weak**: Visual rendering untested, assembly doesn't exist, no end-to-end validation
**What's critical**: Get visual rendering working, build assembly layer, measure sync accuracy

The foundation is solid. The hard parts (meaningful animations, precise timing) have good architectural solutions but need implementation and testing.
