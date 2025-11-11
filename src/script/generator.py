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
          "content": "description to aid generation of manim animations",
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
For dynamic Manim scenes in 3Blue1Brown style. Specify WHICH PATTERN to use and describe the progression.

**CRITICAL - Animation Patterns (Choose One)**:

**Pattern 1: Introduce → Elaborate → Apply**
Use for: Introducing new concepts
```json
{
  "type": "animation",
  "content": "Pattern: Introduce→Elaborate→Apply. Show blue circle (mass), add 'Mass' label above it, then add red arrow from left (force) and animate circle moving right (acceleration)",
  "animation_style": "play",
  "position": "center",
  "duration": 4.0,
  "params": {
    "pattern": "progressive_disclosure",
    "colors": {"concept": "BLUE", "force": "RED"}
  }
}
```

**Pattern 2: Equation → Visual → Example**
Use for: Explaining formulas with equation-visual correspondence
```json
{
  "type": "animation",
  "content": "Pattern: Equation→Visual. Show F=ma equation at top (color F red, m blue, a green). Highlight 'm', show blue circle below. Highlight 'F', add red arrow. Highlight 'a', animate circle moving right.",
  "animation_style": "play",
  "position": "center",
  "duration": 5.0,
  "params": {
    "pattern": "equation_visual",
    "equation_colors": {"F": "RED", "m": "BLUE", "a": "GREEN"}
  }
}
```

**Pattern 3: Transform Concept**
Use for: Showing how ideas relate and evolve
```json
{
  "type": "animation",
  "content": "Pattern: Transform. Show text 'Objects resist change', morph to 'Newton's First Law', morph to equation 'v = constant when ΣF = 0'",
  "animation_style": "play",
  "position": "center",
  "duration": 3.5,
  "params": {
    "pattern": "transform_concept"
  }
}
```

**Pattern 4: Compare & Contrast**
Use for: Showing differences side-by-side
```json
{
  "type": "animation",
  "content": "Pattern: Compare. Left side: blue rectangle with 'With Friction' label, moves then slows down. Right side: green rectangle with 'No Friction' label, moves and continues moving.",
  "animation_style": "play",
  "position": "center",
  "duration": 4.0,
  "params": {
    "pattern": "compare_contrast"
  }
}
```

**Guidelines**:
- ALWAYS specify which pattern to use
- Simple shapes only: Rectangle for car, Circle for ball/mass
- Specify semantic colors: BLUE=concept, RED=force, GREEN=example, YELLOW=highlight
- Describe step-by-step progression
- Mention equation-visual correspondence when relevant

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
**AVOID USING DIAGRAMS** - The diagram renderer is not yet fully implemented. Use simple text or animations instead.

If you MUST use a diagram, keep it extremely simple:
```json
{
  "type": "text",
  "content": "Force Diagram: Weight (down) vs Normal Force (up)",
  "animation_style": "fade",
  "position": "center",
  "params": {
    "font_size": 32
  }
}
```

Better approach: Use animation type with simple shapes to show concepts instead of diagrams.

## Timing Guidelines
- **Narration pace**: ~150 words per minute (2.5 words/second)
- **Visual timing**: Visuals should appear 0.5-1s BEFORE being mentioned in narration
- **Pause after equations**: Add 0.8s pause after complex equations appear
- **Total video**: Aim for 60-90 seconds for most concepts

## Narration Guidelines (TTS-Friendly)
**IMPORTANT**: Narration will be read by text-to-speech. Follow these rules:

1. **Spell out units completely**:
   - ✅ "meters per second" NOT ❌ "m/s"
   - ✅ "kilograms" NOT ❌ "kg"
   - ✅ "six kilogram meters per second" NOT ❌ "6 kg·m/s"

2. **Spell out numbers in context**:
   - ✅ "two kilograms" NOT ❌ "2 kg"
   - ✅ "three meters per second" NOT ❌ "3 m/s"
   - Small numbers (1-20): spell out
   - Large numbers: use digits ("100", "1000")

3. **Avoid special symbols**:
   - NO: · (middle dot), × (times), ² (superscript), → (arrows)
   - ✅ "times" NOT ❌ "×"
   - ✅ "squared" NOT ❌ "²"

4. **Use conversational language**:
   - Natural spoken English
   - Contractions are OK ("it's", "we'll")
   - Short, clear sentences

**Good example**: "Let's see an example. A ball with a mass of two kilograms slides at three meters per second. Its momentum is six kilogram meters per second."

**Bad example**: "Let's see an example. A ball of mass 2 kg sliding with a velocity of 3 m/s. Its momentum is 6 kg·m/s."

## Important Rules
1. **Be specific with animations**: Don't use vague placeholders. Describe exactly what should be animated.
2. **Sync visual timing with narration**: Visuals should support what's being said, appearing just before or during narration.
3. **Keep it simple**: Each visual should have ONE clear purpose. Don't overcomplicate.
4. **Estimate durations accurately**: Consider narration pace + visual animation time.
5. **Use equations for math**: Always use LaTeX for mathematical notation.
6. **Progressive reveal**: Show information gradually, not all at once.

## Example of Good vs Bad Visual Specs

❌ BAD (too vague, not specific about shapes or motion):
{
  "type": "animation",
  "content": "A hockey puck",
  "animation_style": "play"
}

❌ BAD (trying to be realistic with complex details):
{
  "type": "animation",
  "content": "A detailed car with visible engine, chrome bumpers, spinning wheels with treads, and exhaust smoke trailing behind",
  "animation_style": "play"
}

✅ GOOD (simple geometric shape with clear motion and color):
{
  "type": "animation",
  "content": "A blue rectangle representing a car accelerating smoothly from left to right",
  "animation_style": "play",
  "duration": 3.0,
  "params": {}
}

✅ GOOD (specific, simple, clear):
{
  "type": "animation",
  "content": "A gray circle representing a hockey puck sliding at constant speed from left to right",
  "animation_style": "play",
  "duration": 3.0,
  "params": {}
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
