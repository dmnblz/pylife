"""Shared project creation utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

DEFAULT_CONFIG: dict[str, Any] = {
    "gravity": [0, 0],
    "temperature": 0,
}


def setup_config(path: Path) -> Path:
    """Write the default configuration to ``path``.

    Parameters
    ----------
    path:
        Target file path.
    """
    path = Path(path)
    path.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
    return path


def create_project(path: Optional[Path] = None, *, run: bool = False) -> Optional[Path]:
    """Create a project directory and optionally launch the builder.

    Parameters
    ----------
    path:
        Directory to create. If ``None`` no files are written.
    run:
        When ``True`` start the interactive builder.
    """
    project_path = None
    if path is not None:
        project_path = Path(path)
        project_path.mkdir(parents=True, exist_ok=True)
        setup_config(project_path / "config.json")

    if run:
        from importlib import import_module

        BuilderApp = import_module("builder_app").BuilderApp
        app = BuilderApp()
        app.run()

    return project_path
