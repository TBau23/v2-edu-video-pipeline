Success Criteria
Produce a video generation pipeline capable of creating infinite high-quality videos
Measure success with 3 generated videos - 1 for each of Newtons Laws of Motion, each 80-180s long and bug-free
Start from a single prompt
Maintain style consistency across all videos (fonts, colors, pacing, voice, transitions)
Achieve audio-visual sync within ±300 ms
Ensure deterministic re-runs: same inputs yield similar outputs
Enable precise iteration without breaking existing work
Scope
In Scope
Prompt expansion: Input initial video idea → LLM generates detailed specs (equations, narrative, examples, visuals, graphs) → User reviews/edits specs with creative control → Specs feed into video generation pipeline
Script generation: Automatically produce narration text, visuals, locations, and timing
Narration synthesis: Use ElevenLabs or OpenAI TTS synced with visuals at natural pace with pauses
Visual generation: 2D animations with static diagrams (e.g. Manim), graphs and equations (Latex) drawn in real-time
Storyline: Begin each video with real-world animation (rockets, balls, boats) to prime students for the lesson
Sync alignment: Auto-match narration timestamps with text and visuals
Video assembly: Combine narration, overlays, and visuals into 1080p MP4
Style system: Define and apply consistent layout, font, color, and animation tokens
Iteration: Reliable iteration with precise changes maintaining existing parameters; fast low-res preview before final high-res render
UI: Functional interface for inputting prompts and other inputs (JSON, images)
Inputs & Outputs
Inputs
Skill Prompt: Concise text prompt describing skill
Other Spec: Learning objective, script outline, visuals plan, timing cues, style profile, opening narrative, animations, images
Outputs
MP4 (1080p, 30 fps)
JSON (cue alignment metadata)
TXT (narration + on-screen text)
assets/ (auto-generated diagrams and animations)
Style Consistency System
Typography: One consistent font family and size system; all text easily readable
Color Palette: Defined accent and background tones with consistent lighting
Transitions: Uniform duration and easing (250-500 ms)
Equations: LaTeX → SVG with progressive draw; consistent variable color coding
Graph Animations: Sequential appearance of axes, units, data, highlights
Voice Profile: Same tone, pitch, and energy across videos
Overlays: No unintended overlap between text/figures
All style tokens stored in a file for deterministic reproduction.

Architecture Approach
Language: Python (for Manim integration and AI libraries)
Storage: JSON files (human-readable, easy to version control and iterate)
Design Philosophy: Modular pipeline with composable primitives
Key Primitives:
  - Act: fundamental unit representing one video segment (narration + visuals + timing)
  - Script: collection of Acts with metadata (5-act structure: motivation → concept → equation → examples → conclusion)
  - AudioSegment: generated audio for one Act with timing metadata
  - VisualSpec: declarative description of what to show (type, parameters, animation directives)
  - CompiledVideo: final assembled output with sync metadata
Pipeline Layers:
  1. Content Planning: prompt → expanded content structure (acts, concepts, examples)
  2. Script Generation: content structure → Act-by-Act narration with visual directives
  3. Audio Synthesis: Script Acts → audio files + timing data
  4. Visual Generation: VisualSpecs + timing → Manim animations, LaTeX renders
  5. Assembly: all assets + sync metadata → final MP4
Iteration Strategy: Each layer outputs editable JSON/files; can regenerate from any point
Project Structure: src/primitives, src/planning, src/script, src/audio, src/visuals, src/assembly, src/style
Development Priority: Architecture first - focus on clean primitives and interfaces before optimization
