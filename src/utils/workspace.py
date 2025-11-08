"""
Project workspace management utilities.

Handles creation and organization of project directories, ensuring
consistent structure across all video generation projects.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import re

from src.primitives.models import VideoProject, Script
from src.style.config import StyleConfig
from src.utils.io import save_json, load_json, ensure_directory, get_projects_dir


class ProjectWorkspace:
    """Manages a single video project workspace.

    Each project has this structure:
        projects/
          project_name_YYYY_MM_DD/
            project.json       # VideoProject model
            script.json        # Script model (editable)
            style.json         # StyleConfig (editable)
            audio/             # Generated audio files
            visuals/           # Generated animations/images
            renders/           # Rendered videos
              preview.mp4      # Low-res preview
              final.mp4        # High-res final video
            metadata/          # Timing and sync metadata
    """

    def __init__(self, project_id: str):
        """Initialize workspace for a project.

        Args:
            project_id: Unique project identifier
        """
        self.project_id = project_id
        self.root = get_projects_dir() / project_id

        # Define subdirectories
        self.audio_dir = self.root / "audio"
        self.visuals_dir = self.root / "visuals"
        self.renders_dir = self.root / "renders"
        self.metadata_dir = self.root / "metadata"

        # Define key file paths
        self.project_file = self.root / "project.json"
        self.script_file = self.root / "script.json"
        self.style_file = self.root / "style.json"

    def create(self) -> None:
        """Create the workspace directory structure."""
        ensure_directory(self.root)
        ensure_directory(self.audio_dir)
        ensure_directory(self.visuals_dir)
        ensure_directory(self.renders_dir)
        ensure_directory(self.metadata_dir)

    def exists(self) -> bool:
        """Check if this workspace already exists."""
        return self.root.exists() and self.project_file.exists()

    def save_project(self, project: VideoProject) -> None:
        """Save the VideoProject model to disk.

        Args:
            project: VideoProject instance to save
        """
        save_json(project, self.project_file)

    def load_project(self) -> VideoProject:
        """Load the VideoProject model from disk.

        Returns:
            VideoProject instance

        Raises:
            FileNotFoundError: If project file doesn't exist
        """
        return load_json(VideoProject, self.project_file)

    def save_script(self, script: Script) -> None:
        """Save the Script model to disk (user-editable).

        Args:
            script: Script instance to save
        """
        save_json(script, self.script_file)

    def load_script(self) -> Script:
        """Load the Script model from disk.

        Returns:
            Script instance

        Raises:
            FileNotFoundError: If script file doesn't exist
        """
        return load_json(Script, self.script_file)

    def save_style(self, style: StyleConfig) -> None:
        """Save the StyleConfig to disk (user-editable).

        Args:
            style: StyleConfig instance to save
        """
        save_json(style, self.style_file)

    def load_style(self) -> StyleConfig:
        """Load the StyleConfig from disk.

        Returns:
            StyleConfig instance

        Raises:
            FileNotFoundError: If style file doesn't exist
        """
        return load_json(StyleConfig, self.style_file)

    def get_audio_path(self, act_id: str) -> Path:
        """Get the file path for an act's audio.

        Args:
            act_id: Act identifier

        Returns:
            Path to audio file
        """
        return self.audio_dir / f"{act_id}.mp3"

    def get_visual_path(self, act_id: str, visual_index: int) -> Path:
        """Get the file path for a visual asset.

        Args:
            act_id: Act identifier
            visual_index: Index of the visual in the act

        Returns:
            Path to visual file (without extension)
        """
        return self.visuals_dir / f"{act_id}_visual_{visual_index}"

    def get_preview_path(self) -> Path:
        """Get path for preview video."""
        return self.renders_dir / "preview.mp4"

    def get_final_path(self) -> Path:
        """Get path for final high-res video."""
        return self.renders_dir / "final.mp4"


def generate_project_id(topic: str) -> str:
    """Generate a unique project ID from a topic.

    Args:
        topic: Video topic or title

    Returns:
        Project ID in format: topic_slug_YYYY_MM_DD_HHMMSS

    Example:
        "Newton's First Law" -> "newtons_first_law_2025_01_07_143022"
    """
    # Convert to lowercase and replace non-alphanumeric with underscores
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")

    # Truncate if too long
    if len(slug) > 50:
        slug = slug[:50].rstrip("_")

    # Add timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")

    return f"{slug}_{timestamp}"


def create_project(
    script: Script,
    style: Optional[StyleConfig] = None
) -> ProjectWorkspace:
    """Create a new video project workspace.

    Args:
        script: Generated script for the video
        style: Style configuration (defaults to default preset)

    Returns:
        ProjectWorkspace instance for the new project
    """
    # Generate project ID
    project_id = generate_project_id(script.topic)

    # Create workspace
    workspace = ProjectWorkspace(project_id)
    workspace.create()

    # Use default style if none provided
    if style is None:
        style = StyleConfig.load_preset("default")

    # Create VideoProject model
    project = VideoProject(
        project_id=project_id,
        script=script,
        workspace_path=workspace.root,
        status="script_only"
    )

    # Save everything
    workspace.save_project(project)
    workspace.save_script(script)
    workspace.save_style(style)

    return workspace


def load_project(project_id: str) -> ProjectWorkspace:
    """Load an existing project workspace.

    Args:
        project_id: Project identifier

    Returns:
        ProjectWorkspace instance

    Raises:
        FileNotFoundError: If project doesn't exist
    """
    workspace = ProjectWorkspace(project_id)

    if not workspace.exists():
        raise FileNotFoundError(f"Project not found: {project_id}")

    return workspace


def list_projects() -> list[str]:
    """List all project IDs in the projects directory.

    Returns:
        List of project IDs (directory names)
    """
    projects_dir = get_projects_dir()

    return [
        p.name for p in projects_dir.iterdir()
        if p.is_dir() and (p / "project.json").exists()
    ]
