## Audio Synthesis System

Converts Act narration text into audio files with precise timing metadata for synchronization.

## Architecture

```
Act.narration
    ↓
TTSProvider (OpenAI/ElevenLabs)
    ↓
Audio file (.mp3) + duration
    ↓
TimingExtractor (estimation or forced alignment)
    ↓
Word-level timestamps
    ↓
AudioSegment (saved to workspace)
```

## Components

### 1. providers.py
**Purpose**: TTS provider abstraction and implementations

**Classes**:
- `TTSProvider` (ABC): Abstract interface for TTS providers
- `OpenAITTSProvider`: OpenAI text-to-speech implementation
- `ElevenLabsTTSProvider`: ElevenLabs TTS implementation
- `get_provider()`: Factory function

**Features**:
- Unified API across providers
- Audio file generation
- Duration extraction
- Cache key generation

**OpenAI TTS**:
- Voices: alloy, echo, fable, onyx, nova, shimmer
- Models: tts-1 (fast), tts-1-hd (quality)
- Speed: 0.25-4.0x
- Output: MP3 format

**Note**: OpenAI TTS doesn't currently provide word-level timestamps,  so we use estimation as fallback.

### 2. timing.py
**Purpose**: Word-level timestamp extraction and estimation

**Classes**:
- `TimingExtractor`: Estimates word timing from text + duration

**Key methods**:
- `estimate_timestamps()`: Fallback when provider doesn't give timestamps
- `estimate_duration()`: Predict audio duration from text
- `adjust_timing_for_sync()`: Scale timestamps to match target duration

**Timing Strategy**:
- Accounts for natural pauses at punctuation
- Configurable speaking rate (default: 150 WPM)
- Returns `WordTimestamp` objects with start/end times

**Accuracy**:
- Estimation: ±500ms per word (depends on uniform speaking pace assumption)
- Forced alignment (TODO): ±50ms per word (much better for sync)

### 3. synthesizer.py
**Purpose**: Main audio synthesis system

**Class**: `AudioSynthesizer`
- Orchestrates TTS providers and timing extraction
- Handles caching to avoid regenerating unchanged audio
- Integrates with StyleConfig for voice settings
- Creates AudioSegment objects with all metadata

**Usage**:
```python
synthesizer = AudioSynthesizer(
    provider="openai",
    style=style_config
)

# Single act
audio_segment = synthesizer.synthesize_act(
    act=act,
    output_path=Path("audio/act_1.mp3")
)

# Entire script
audio_segments = synthesizer.synthesize_script(
    script=script,
    output_dir=Path("audio/")
)
```

**Caching**:
- Cache key: hash(narration + voice + speed + provider)
- Stored in `.audio_cache/` directory
- Avoids re-synthesizing unchanged narration
- Critical for iteration workflow

### 4. Word Timestamps

**Structure**:
```python
WordTimestamp(
    word="Hello",
    start=0.0,    # seconds
    end=0.4       # seconds
)
```

**Use cases**:
- Sync visuals to specific words in narration
- Highlight text as it's spoken
- Precisely time equation reveals
- Debug timing issues

**Example**:
```
Narration: "Imagine you're in a car."
Timestamps:
  - "Imagine" : 0.0 - 0.5s
  - "you're"  : 0.5 - 0.8s
  - "in"      : 0.8 - 1.0s
  - "a"       : 1.0 - 1.1s
  - "car"     : 1.1 - 1.5s
```

## Integration with StyleConfig

The synthesizer uses StyleConfig for voice settings:

```python
style.voice.provider      # "openai" or "elevenlabs"
style.voice.voice_id      # "alloy", "nova", etc.
style.voice.speed         # 0.5 - 2.0 (speed multiplier)
style.voice.pause_markers # {".": 0.5, ",": 0.3, ...}
```

These settings ensure consistent voice across all videos.

## Workflow

### 1. Generate Audio for Script

```bash
python examples/generate_audio.py
```

This:
1. Loads most recent project
2. Synthesizes audio for all Acts
3. Saves to `workspace/audio/{act_id}.mp3`
4. Updates project with AudioSegments
5. Saves timing metadata

### 2. Iteration

If you edit a script's narration:

```python
# Load workspace
workspace = load_project("project_id")

# Edit script.json manually or programmatically
script = workspace.load_script()
script.acts[2].narration = "New narration text..."
workspace.save_script(script)

# Regenerate only changed acts
synthesizer = AudioSynthesizer(style=workspace.load_style())
audio_segment = synthesizer.synthesize_act(
    script.acts[2],
    workspace.audio_dir / "act_3_equation.mp3"
)
```

Cache ensures only the changed act is regenerated.

### 3. Caching Behavior

**Cache hit** (narration unchanged):
- Instant retrieval from `.audio_cache/`
- No API call to TTS provider

**Cache miss** (narration changed):
- Synthesize new audio
- Save to cache for future use

**Clear cache**:
```bash
rm -rf .audio_cache/
```

## Testing

To test audio synthesis:

```bash
# Set API key
export OPENAI_API_KEY="your-key"

# Generate a script first
python examples/generate_script.py

# Generate audio for that script
python examples/generate_audio.py
```

## Timing Accuracy

### Current Implementation (Estimation)
- **Accuracy**: ±500ms per word
- **Method**: Divide duration evenly among words, account for pauses
- **Limitation**: Assumes uniform speaking pace
- **Good enough for**: Basic synchronization, prototyping

### Future: Forced Alignment
- **Accuracy**: ±50ms per word
- **Method**: Align audio with text using speech recognition
- **Tools**: Gentle, aeneas, Montreal Forced Aligner
- **Required for**: ±300ms sync accuracy target

**Implementing forced alignment**:
```python
# In timing.py
def align_forced(audio_path, text):
    # Option 1: Use aeneas (Python library)
    from aeneas.executetask import ExecuteTask
    # ... alignment code ...

    # Option 2: Use Gentle (Docker/API)
    # POST audio + text to Gentle API
    # Parse JSON response for timestamps

    return word_timestamps
```

## Current Limitations & TODOs

### ✅ Implemented
- OpenAI TTS integration
- Multiple voice support
- Speed control
- Caching system
- Timestamp estimation
- Workspace integration
- Natural pause calculation

### 🔲 TODO
- **Forced alignment**: Implement for better timing accuracy
- **ElevenLabs testing**: Verify ElevenLabs integration works
- **SSML support**: Add pause markers for providers that support it
- **Error recovery**: Handle TTS API failures gracefully
- **Progress tracking**: Show progress for long scripts
- **Batch synthesis**: Parallelize audio generation for multiple acts
- **Audio preview**: Quick low-quality synthesis for iteration

## Key Insights

### Why Caching Matters
Without caching, every iteration requires:
- API calls ($$$)
- Wait time (~2-5s per act)
- Bandwidth (audio download)

With caching:
- Instant for unchanged acts
- Only regenerate what changed
- Free iterations

### Why Word Timestamps Matter
For ±300ms sync accuracy, we need to know:
- When each word is spoken
- When to trigger visual animations
- How to align equation reveals with narration

Estimation gets us ~80% there, but forced alignment is needed for production quality.

### Provider Choice

**OpenAI TTS**:
- ✅ Fast (2-3s per act)
- ✅ Cheap ($0.015/1K chars)
- ✅ Easy integration
- ❌ No word timestamps (yet)
- ❌ Voice quality is good but not amazing

**ElevenLabs**:
- ✅ Excellent voice quality
- ✅ More natural intonation
- ❌ Slower (5-8s per act)
- ❌ More expensive (~$0.30/1K chars)
- ❌ Timestamp support unclear

**Recommendation**: Start with OpenAI for MVP, add ElevenLabs as premium option.

## Next Steps

1. **Test end-to-end**: Script → Audio → Visuals
2. **Implement forced alignment** for production accuracy
3. **Measure sync accuracy**: Validate ±300ms target
4. **Optimize caching**: Add cache invalidation logic
5. **Add preview mode**: Low-quality fast synthesis
