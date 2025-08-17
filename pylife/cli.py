"""Command line interface for pylife."""
from __future__ import annotations

from pathlib import Path
import typer

from .core import create_project, setup_config

app = typer.Typer(help="Utilities for working with pylife projects")


@app.command()
def create(path: Path, run: bool = typer.Option(False, help="Launch builder after setup")):
    """Create a new project directory at PATH."""
    create_project(path, run=run)
    typer.echo(f"Created project at {path}")


@app.command()
def config(path: Path):
    """Write a default configuration file to PATH."""
    setup_config(path)
    typer.echo(f"Wrote config to {path}")


if __name__ == "__main__":  # pragma: no cover - manual invocation
    app()
