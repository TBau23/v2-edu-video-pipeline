"""
File I/O utilities for saving and loading primitive models as JSON.

These utilities handle serialization/deserialization of Pydantic models
with proper path handling and error management.
"""

import json
from pathlib import Path
from typing import TypeVar, Type
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def save_json(model: BaseModel, path: Path | str, indent: int = 2) -> None:
    """Save a Pydantic model to a JSON file.

    Args:
        model: Pydantic model instance to save
        path: File path to save to
        indent: JSON indentation (default: 2 for readability)

    Raises:
        IOError: If file cannot be written
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        # Use model_dump for Pydantic v2 compatibility
        json.dump(model.model_dump(mode="json"), f, indent=indent, ensure_ascii=False)


def load_json(model_class: Type[T], path: Path | str) -> T:
    """Load a Pydantic model from a JSON file.

    Args:
        model_class: The Pydantic model class to instantiate
        path: File path to load from

    Returns:
        Instance of model_class populated with data from JSON

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid or doesn't match model schema
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return model_class.model_validate(data)


def save_pretty_json(data: dict, path: Path | str) -> None:
    """Save a dictionary as pretty-printed JSON.

    Useful for saving arbitrary data that doesn't have a Pydantic model.

    Args:
        data: Dictionary to save
        path: File path to save to
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_raw_json(path: Path | str) -> dict:
    """Load raw JSON data as a dictionary.

    Args:
        path: File path to load from

    Returns:
        Dictionary with JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_directory(path: Path | str) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_project_root() -> Path:
    """Get the root directory of the project.

    Returns:
        Path to the project root (where src/ is located)
    """
    # Navigate up from this file: src/utils/io.py -> project root
    return Path(__file__).parent.parent.parent


def get_projects_dir() -> Path:
    """Get the projects directory where user projects are stored.

    Returns:
        Path to the projects/ directory
    """
    projects_dir = get_project_root() / "projects"
    ensure_directory(projects_dir)
    return projects_dir


def get_styles_dir() -> Path:
    """Get the styles directory where style configs are stored.

    Returns:
        Path to the src/style/presets/ directory
    """
    styles_dir = get_project_root() / "src" / "style" / "presets"
    ensure_directory(styles_dir)
    return styles_dir
