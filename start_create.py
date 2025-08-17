"""Entry point for launching the interactive builder."""
from __future__ import annotations

from pylife.core import create_project


def main() -> None:
    """Launch the builder using shared project utilities."""
    create_project(run=True)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
