"""
Script generation using LLM.

This module takes a user prompt and generates a complete Script with:
- 5-act structure (motivation → concept → equation → examples → conclusion)
- Detailed narration for each act
- Actionable VisualSpecs that can be rendered by Manim
- Timing hints for audio-visual synchronization

The key challenge: Visual specs must be detailed enough to actually render,
not vague placeholders like "car_animation".
"""

import os
import json
from typing import Optional
from openai import OpenAI

from src.primitives.models import Script, Act, VisualSpec


# System prompt that teaches the LLM about our primitives and constraints
SCRIPT_GENERATION_SYSTEM_PROMPT = """You are an expert educational video script writer. Your job is to create engaging, pedagogically sound video scripts for educational content.

## Output Format
You must output a valid JSON object matching this structure:
{
  "title": "Video Title",
  "topic": "brief topic description",
  "acts": [
    {
      "id": "act_1_motivation",
      "narration": "The spoken narration text...",
      "visuals": [
        {
          "type": "equation|graph|animation|diagram|text",
          "content": "detailed content description",
          "animation_style": "draw|fade|write|play",
          "position": "center|top|bottom|left|right",
          "duration": 2.0,  // optional, in seconds
          "params": {}  // type-specific parameters
        }
      ],
      "estimated_duration": 12.0,
      "purpose": "what this act accomplishes"
    }
  ],
  "source_prompt": "the original user prompt",
  "style_profile": "default"
}

## Video Structure (Flexible Acts)
Videos should follow this pedagogical pattern (typically 3-7 acts):

**Recommended flow:**
1. **Motivation/Intro** (10-15 seconds)
   - Hook with relatable real-world scenario
   - Make viewers care about the topic
   - Use engaging visuals (simple animations or scenarios)

2. **Concept Explanation** (8-12 seconds)
   - State the main concept clearly
   - High-level understanding
   - Use text overlays for key terms

3. **Equation/Formula** (6-10 seconds, if applicable)
   - Present mathematical representation
   - Explain what each component means
   - Use equation visuals with progressive reveal

4. **Examples** (15-25 seconds)
   - 2-3 concrete examples building intuition
   - Each example can be its own act if complex
   - Connect back to the core concept

5. **Conclusion/Applications** (8-12 seconds)
   - Summarize key takeaway
   - Connect to real-world applications
   - Leave viewer with clear understanding

**Flexibility**: Adapt the number of acts based on content complexity. Simple topics may need 3-4 acts, complex topics may need 6-7.

## Visual Types and How to Use Them

### 1. equation
For mathematical formulas. Use LaTeX syntax.
```json
{
  "type": "equation",
  "content": "F = ma",  // LaTeX string
  "animation_style": "write",  // write, fade, draw
  "position": "center",
  "params": {
    "color": "equation_color",  // uses style config
    "font_size": 48
  }
}
```

### 2. text
For titles, labels, key concepts.
```json
{
  "type": "text",
  "content": "Newton's First Law",
  "animation_style": "fade",  // fade, write
  "position": "top",
  "params": {
    "font_size": 42,
    "color": "accent"
  }
}
```

### 3. animation
For dynamic Manim scenes. Be VERY SPECIFIC about what to animate.
Instead of: "car_animation"
Use: "car_accelerating_from_rest"

Describe the animation clearly enough that a renderer could create it:
```json
{
  "type": "animation",
  "content": "A simple car (rectangle with circles for wheels) at rest, then accelerating to the right. Show motion lines behind it.",
  "animation_style": "play",
  "position": "center",
  "duration": 4.0,
  "params": {
    "objects": ["car", "motion_lines"],
    "motion": "accelerate_right",
    "start_velocity": 0,
    "end_velocity": 5
  }
}
```

### 4. graph
For plotting data, functions, or relationships.
```json
{
  "type": "graph",
  "content": "position vs time for constant velocity",
  "animation_style": "draw",
  "position": "center",
  "duration": 3.0,
  "params": {
    "x_label": "Time (s)",
    "y_label": "Position (m)",
    "x_range": [0, 10],
    "y_range": [0, 50],
    "function": "5*x",  // linear function
    "plot_type": "line"
  }
}
```

### 5. diagram
For static illustrations with labels.
```json
{
  "type": "diagram",
  "content": "free body diagram of book on table",
  "animation_style": "fade",
  "position": "center",
  "params": {
    "objects": ["book", "table"],
    "forces": [
      {"name": "Weight", "direction": "down", "magnitude": "mg"},
      {"name": "Normal", "direction": "up", "magnitude": "N"}
    ],
    "labels": true
  }
}
```

## Timing Guidelines
- **Narration pace**: ~150 words per minute (2.5 words/second)
- **Visual timing**: Visuals should appear 0.5-1s BEFORE being mentioned in narration
- **Pause after equations**: Add 0.8s pause after complex equations appear
- **Total video**: Aim for 60-90 seconds for most concepts

## Important Rules
1. **Be specific with animations**: Don't use vague placeholders. Describe exactly what should be animated.
2. **Sync visual timing with narration**: Visuals should support what's being said, appearing just before or during narration.
3. **Keep it simple**: Each visual should have ONE clear purpose. Don't overcomplicate.
4. **Estimate durations accurately**: Consider narration pace + visual animation time.
5. **Use equations for math**: Always use LaTeX for mathematical notation.
6. **Progressive reveal**: Show information gradually, not all at once.

## Example of Good vs Bad Visual Specs

❌ BAD (too vague):
{
  "type": "animation",
  "content": "hockey_puck",
  "animation_style": "play"
}

✅ GOOD (specific and actionable):
{
  "type": "animation",
  "content": "A hockey puck (gray disk) sliding from left to right across ice (light blue surface) at constant velocity, with faint motion lines trailing behind it",
  "animation_style": "play",
  "duration": 3.0,
  "params": {
    "object_type": "disk",
    "color": "gray",
    "motion": "constant_velocity",
    "direction": "right",
    "velocity": 3,
    "show_motion_lines": true
  }
}
"""


def generate_script(
    user_prompt: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o",
) -> Script:
    """Generate a complete video script from a user prompt.

    Uses OpenAI to generate a 5-act script with detailed narration and
    actionable visual specifications.

    Args:
        user_prompt: User's description of what they want to teach
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        model: OpenAI model to use (default: gpt-4o for vision and reasoning)

    Returns:
        Script object with all acts, narration, and visual specs

    Raises:
        ValueError: If API key is not provided or found in environment
        Exception: If LLM generation fails
    """
    # Get API key
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key required. Set OPENAI_API_KEY environment variable "
            "or pass api_key parameter."
        )

    client = OpenAI(api_key=api_key)

    # Construct user message
    user_message = f"""Create an educational video script for the following topic:

{user_prompt}

Generate a complete 5-act script following the structure and guidelines provided.
Focus on creating detailed, actionable visual specifications that can be rendered.

Output valid JSON only, no additional text."""

    # Call OpenAI
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SCRIPT_GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Parse response
        script_data = json.loads(response.choices[0].message.content)

        # Validate and create Script object (Pydantic will validate)
        script = Script.model_validate(script_data)

        return script

    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        raise Exception(f"Script generation failed: {e}")


def generate_script_from_structure(
    topic: str,
    acts_outline: list[dict],
    api_key: Optional[str] = None,
    model: str = "gpt-4o",
) -> Script:
    """Generate script from a pre-defined act structure.

    Useful for when the user wants to iterate on specific acts
    or provide their own structure.

    Args:
        topic: Video topic
        acts_outline: List of act descriptions/outlines
        api_key: OpenAI API key
        model: OpenAI model to use

    Returns:
        Script object with generated narration and visuals
    """
    # TODO: Implement this for iteration workflows
    # For now, defer to generate_script
    prompt = f"Create a video about {topic} covering these points: {acts_outline}"
    return generate_script(prompt, api_key, model)
