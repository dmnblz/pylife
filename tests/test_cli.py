import json
from pathlib import Path
import sys

from typer.testing import CliRunner

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pylife.cli import app
from pylife.core import DEFAULT_CONFIG


runner = CliRunner()


def test_config_command(tmp_path: Path) -> None:
    cfg_path = tmp_path / "conf.json"
    result = runner.invoke(app, ["config", str(cfg_path)])
    assert result.exit_code == 0
    assert cfg_path.exists()
    data = json.loads(cfg_path.read_text())
    assert data == DEFAULT_CONFIG


def test_create_command(tmp_path: Path) -> None:
    result = runner.invoke(app, ["create", str(tmp_path)])
    assert result.exit_code == 0
    cfg = tmp_path / "config.json"
    assert cfg.exists()
    data = json.loads(cfg.read_text())
    assert data == DEFAULT_CONFIG
