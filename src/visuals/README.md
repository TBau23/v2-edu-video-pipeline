# Visual Rendering System

The visual rendering system converts declarative `VisualSpec` objects into actual Manim animations.

## Architecture

```
VisualSpec (JSON)
    ↓
VisualRenderer (parser)
    ↓
Manim Scene (code generation)
    ↓
SceneExecutor (rendering)
    ↓
Video file (.mp4)
```

## Components

### 1. renderer.py
**Purpose**: Parse VisualSpecs and generate Manim Scene classes

**Key class**: `VisualRenderer`
- Takes an Act with multiple VisualSpecs
- Generates a Scene class that renders all visuals with proper timing
- Handles 5 visual types: equation, text, graph, animation, diagram

**Usage**:
```python
renderer = VisualRenderer(style, output_dir)
result = renderer.render_act(act, target_duration=12.5)
```

### 2. animations.py
**Purpose**: Library of reusable animation primitives

**Key classes**:
- `PhysicsAnimations`: Physics scenarios (cars, pucks, objects at rest)
- `MathAnimations`: Math visualizations (equations, plots)
- `AnimationLibrary`: Central registry for looking up animations by name

**Philosophy**: Instead of generating animations from scratch every time, we build a curated library of high-quality, pedagogically useful animations.

**Available animations**:
- `car_accelerating`: Car accelerating from rest
- `hockey_puck_sliding`: Puck at constant velocity
- `object_at_rest`: Object on surface (optional force arrows)
- `person_in_braking_car`: Person lurching forward
- `equation_progressive_reveal`: Reveal equation parts sequentially
- `function_plot_animated`: Animate drawing a function graph

**Adding new animations**:
```python
@staticmethod
def my_animation(param1, param2, duration=2.0, **kwargs):
    # Create Manim mobjects
    obj = Circle()

    # Define animations
    animations = [FadeIn(obj)]

    return obj, animations, duration

# Register it
AnimationLibrary.register("my_animation", my_animation)
```

### 3. executor.py
**Purpose**: Execute Manim rendering programmatically

**Key class**: `SceneExecutor`
- Configures Manim settings (resolution, quality, output path)
- Renders Scene classes to video files
- Supports two approaches:
  1. Direct API (cleaner but trickier)
  2. CLI invocation (more robust)

**Usage**:
```python
executor = SceneExecutor(output_dir, quality="medium_quality")
output_path = executor.render_scene(MyScene, "output_name", preview=False)
```

## Visual Types

### equation
LaTeX mathematical expressions

**VisualSpec**:
```json
{
  "type": "equation",
  "content": "F = ma",
  "animation_style": "write",
  "position": "center",
  "params": {
    "color": "equation_color",
    "font_size": 48
  }
}
```

**Rendered as**: `MathTex` object with Write/FadeIn animation

### text
Text overlays (titles, labels, captions)

**VisualSpec**:
```json
{
  "type": "text",
  "content": "Newton's First Law",
  "animation_style": "fade",
  "position": "top",
  "params": {
    "font_size": 42,
    "color": "accent"
  }
}
```

**Rendered as**: `Text` object with animation

### graph
Function plots with axes

**VisualSpec**:
```json
{
  "type": "graph",
  "content": "position vs time",
  "animation_style": "draw",
  "params": {
    "x_label": "Time (s)",
    "y_label": "Position (m)",
    "x_range": [0, 10, 1],
    "y_range": [0, 50, 5],
    "function": "5*x"
  }
}
```

**Rendered as**: `Axes` + function plot

### animation
Custom physics/math animations from the library

**VisualSpec**:
```json
{
  "type": "animation",
  "content": "car_accelerating",
  "animation_style": "play",
  "params": {
    "start_pos": [-4, 0, 0],
    "end_pos": [4, 0, 0],
    "acceleration": 1.5,
    "show_motion_lines": true
  }
}
```

**Rendered as**: Looks up animation in `AnimationLibrary` and executes it

### diagram
Static illustrations with labels (force diagrams, etc.)

**VisualSpec**:
```json
{
  "type": "diagram",
  "content": "free body diagram",
  "params": {
    "objects": ["book", "table"],
    "forces": [
      {"name": "Weight", "direction": "down"},
      {"name": "Normal", "direction": "up"}
    ]
  }
}
```

**Rendered as**: Composed shapes with arrows and labels

## Timing Strategy

**Challenge**: Visuals must sync precisely with audio narration.

**Approach**:
1. Each VisualSpec has optional `duration` field
2. If not specified, duration is divided equally among visuals in an Act
3. Renderer uses actual audio duration (from AudioSegment) as target
4. Manim `run_time` parameter controls animation speed

**Example**:
```python
# Act duration: 12.0s (from audio)
# 3 visuals in the act
# Each gets: 12.0 / 3 = 4.0s

visual1: duration = 4.0s
visual2: duration = 4.0s
visual3: duration = 4.0s
```

**Fine-tuning**: Edit VisualSpec duration in `script.json` to adjust timing.

## Style Integration

Renderer uses `StyleConfig` for consistency:

```python
# Colors
equation_color = style.colors.equation_color
text_color = style.colors.primary
background = style.colors.background

# Typography
font_size = style.typography.equation_size
font_family = style.typography.font_family

# Timing
fade_duration = style.animation.fade_duration
write_duration = style.animation.write_duration
```

## Current Limitations & TODOs

### ✅ Implemented
- Basic equation rendering (LaTeX → MathTex)
- Text rendering with positioning
- Graph rendering with axes
- Animation library architecture
- Scene composition (multiple visuals per act)
- Style integration

### 🔲 TODO
- **Complete graph rendering**: Actually plot functions, not just axes
- **Animation parameter parsing**: Map VisualSpec params to animation args
- **Scene executor**: Test actual Manim rendering (API approach)
- **Diagram rendering**: Build force diagram system
- **Motion lines**: Add visual effects (motion blur, trails)
- **Expand animation library**: More physics scenarios
- **Error handling**: Gracefully handle invalid specs
- **Preview mode**: Low-res fast rendering for iteration
- **Caching**: Don't re-render unchanged visuals

## Testing

To test the rendering system:

```bash
# Test scene executor
python src/visuals/executor.py

# Test with example project
# (TODO: create render_example.py)
```

## Next Steps

1. **Complete graph rendering** - Actually plot the function
2. **Test executor with real Manim scenes**
3. **Build diagram rendering system**
4. **Create integration test**: script.json → rendered videos
5. **Optimize timing**: Profile rendering speed
6. **Add more animations to library**

## Key Insight

The hardest part isn't rendering equations or text - Manim does that well. The hardest part is:

1. **Creating meaningful physics animations** that teach concepts
2. **Parsing VisualSpec params** into animation parameters
3. **Timing precision** - ensuring visuals appear at the right moment

That's why we built the animation library - to curate high-quality pedagogical animations that the LLM can reference by name, with parameters to customize them.
