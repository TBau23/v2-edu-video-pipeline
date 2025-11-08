"""
Example: Creating a simple video project using the primitives.

This demonstrates how to:
1. Create Acts with narration and visual specs
2. Build a Script from those Acts
3. Create a project workspace
4. Save everything as editable JSON files
"""

from src.primitives.models import Act, Script, VisualSpec
from src.style.config import StyleConfig
from src.utils.workspace import create_project


def main():
    """Create a simple example project for Newton's First Law."""

    # Define the 5 acts for the video
    acts = [
        Act(
            id="act_1_motivation",
            narration=(
                "Imagine you're sitting in a car at a red light. "
                "When the light turns green and the car accelerates forward, "
                "you feel pushed back into your seat. But why? "
                "The answer lies in one of the most fundamental principles of physics."
            ),
            visuals=[
                VisualSpec(
                    type="animation",
                    content="car_at_stoplight_then_accelerating",
                    animation_style="play",
                    position="center",
                    params={"duration": 4.0}
                )
            ],
            purpose="Hook the viewer with a relatable scenario",
            estimated_duration=12.0
        ),

        Act(
            id="act_2_concept",
            narration=(
                "Newton's First Law of Motion states that an object at rest stays at rest, "
                "and an object in motion stays in motion at constant velocity, "
                "unless acted upon by an external force. "
                "This property is called inertia."
            ),
            visuals=[
                VisualSpec(
                    type="text",
                    content="Newton's First Law of Motion",
                    animation_style="write",
                    position="top",
                    params={"font_size": 48, "color": "accent"}
                ),
                VisualSpec(
                    type="text",
                    content="Objects resist changes to their motion",
                    animation_style="fade",
                    position="center",
                    params={"font_size": 36}
                )
            ],
            purpose="Introduce the core concept",
            estimated_duration=10.0
        ),

        Act(
            id="act_3_equation",
            narration=(
                "Mathematically, we express this as F equals m times a. "
                "When the net force F is zero, the acceleration a is also zero, "
                "meaning velocity remains constant."
            ),
            visuals=[
                VisualSpec(
                    type="equation",
                    content=r"\sum F = ma",
                    animation_style="write",
                    position="center",
                    params={"color": "equation_color"}
                ),
                VisualSpec(
                    type="equation",
                    content=r"F = 0 \Rightarrow a = 0",
                    animation_style="write",
                    position="center",
                    duration=2.0
                )
            ],
            purpose="Show the mathematical relationship",
            estimated_duration=8.0
        ),

        Act(
            id="act_4_examples",
            narration=(
                "Let's look at three examples. "
                "First, a hockey puck sliding on ice keeps moving in a straight line "
                "because there's minimal friction. "
                "Second, you lurch forward when a car brakes because your body "
                "wants to maintain its forward motion. "
                "Third, a book on a table stays at rest until you push it."
            ),
            visuals=[
                VisualSpec(
                    type="animation",
                    content="hockey_puck_sliding",
                    animation_style="play",
                    position="center"
                ),
                VisualSpec(
                    type="animation",
                    content="person_in_braking_car",
                    animation_style="play",
                    position="center"
                ),
                VisualSpec(
                    type="animation",
                    content="book_on_table",
                    animation_style="play",
                    position="center"
                )
            ],
            purpose="Build intuition with concrete examples",
            estimated_duration=18.0
        ),

        Act(
            id="act_5_conclusion",
            narration=(
                "Inertia is everywhere in our daily lives. "
                "Understanding Newton's First Law helps us predict how objects move "
                "and explains why seatbelts, airbags, and crumple zones are so important. "
                "Objects naturally resist changes to their motion - that's the essence of inertia."
            ),
            visuals=[
                VisualSpec(
                    type="text",
                    content="Inertia: Objects resist changes to their motion",
                    animation_style="fade",
                    position="center",
                    params={"font_size": 42}
                )
            ],
            purpose="Connect to real-world applications and conclude",
            estimated_duration=12.0
        )
    ]

    # Create the script
    script = Script(
        title="Newton's First Law of Motion",
        topic="inertia and constant velocity",
        source_prompt="Create an educational video explaining Newton's First Law with real-world examples",
        acts=acts,
        style_profile="default"
    )

    # Create the project workspace
    print(f"Creating project for: {script.title}")
    print(f"Total estimated duration: {script.estimated_total_duration:.1f} seconds")
    print(f"Number of acts: {script.act_count}")

    workspace = create_project(script)

    print(f"\nProject created at: {workspace.root}")
    print("\nGenerated files:")
    print(f"  - {workspace.project_file.name} (project metadata)")
    print(f"  - {workspace.script_file.name} (editable script)")
    print(f"  - {workspace.style_file.name} (editable style config)")
    print("\nYou can now edit the script.json file to iterate on the content!")

    return workspace


if __name__ == "__main__":
    workspace = main()
