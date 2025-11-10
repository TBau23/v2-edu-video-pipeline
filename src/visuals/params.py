"""
Parameter conversion utilities for animations.

Converts VisualSpec JSON parameters to Manim-compatible Python types.
"""

import numpy as np
from manim import (
    UP, DOWN, LEFT, RIGHT,
    BLUE, RED, GREEN, YELLOW, GRAY, DARK_GRAY, MAROON_B, BLUE_E, ORANGE,
    linear, smooth, rush_into, rush_from, there_and_back
)


# Manim direction constants
DIRECTION_CONSTANTS = {
    "UP": UP,
    "DOWN": DOWN,
    "LEFT": LEFT,
    "RIGHT": RIGHT,
    "ORIGIN": np.array([0, 0, 0]),
}

# Manim color constants
COLOR_CONSTANTS = {
    "BLUE": BLUE,
    "RED": RED,
    "GREEN": GREEN,
    "YELLOW": YELLOW,
    "GRAY": GRAY,
    "DARK_GRAY": DARK_GRAY,
    "MAROON_B": MAROON_B,
    "BLUE_E": BLUE_E,
    "ORANGE": ORANGE,
}

# Manim rate function constants
RATE_FUNC_CONSTANTS = {
    "linear": linear,
    "smooth": smooth,
    "rush_into": rush_into,
    "rush_from": rush_from,
    "there_and_back": there_and_back,
}

# Combined constants lookup
MANIM_CONSTANTS = {
    **DIRECTION_CONSTANTS,
    **COLOR_CONSTANTS,
    **RATE_FUNC_CONSTANTS,
}


def convert_param_value(key: str, value):
    """Convert a single parameter value to Manim-compatible type.

    Args:
        key: Parameter name (used for context)
        value: Parameter value from JSON

    Returns:
        Converted value suitable for Manim
    """
    # Handle None
    if value is None:
        return None

    # Handle lists -> numpy arrays (for positions)
    if isinstance(value, list):
        if key.endswith("_pos") or key.endswith("_range"):
            # Position or range: convert to numpy array
            return np.array(value)
        else:
            # Keep as list (might be list of strings, etc.)
            return value

    # Handle string constants
    if isinstance(value, str):
        # Check if it's a known Manim constant
        if value in MANIM_CONSTANTS:
            return MANIM_CONSTANTS[value]

        # Check if it's a hex color (e.g., "#ff0000")
        if value.startswith("#"):
            return value

        # Otherwise, keep as string
        return value

    # Handle numbers and booleans (pass through)
    return value


def convert_params(params: dict) -> dict:
    """Convert VisualSpec params dict to animation function kwargs.

    Handles:
    - Lists → numpy arrays for positions
    - Strings → Manim constants (UP, DOWN, BLUE, etc.)
    - Numbers, booleans → pass through

    Args:
        params: Dictionary of parameters from VisualSpec

    Returns:
        Dictionary with converted values

    Example:
        Input:  {"start_pos": [-4, 0, 0], "color": "BLUE"}
        Output: {"start_pos": array([-4, 0, 0]), "color": BLUE}
    """
    if not params:
        return {}

    converted = {}
    for key, value in params.items():
        converted[key] = convert_param_value(key, value)

    return converted


def merge_params_with_defaults(params: dict, duration: float) -> dict:
    """Merge converted params with default values needed by animations.

    Args:
        params: Converted parameters from VisualSpec
        duration: Duration to use for the animation

    Returns:
        Parameters with duration included
    """
    merged = params.copy()
    merged["duration"] = duration
    return merged
