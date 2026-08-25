"""Command-line behaviour, exit statuses, and the built-in default configuration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from galaxy_structure import __version__
from galaxy_structure.cli import main
from galaxy_structure.config import DEFAULT_CONFIG_MAPPING
from galaxy_structure.demo import ARTIFACT_PATHS, MANIFEST_NAME
from galaxy_structure.manifest import read_manifest, validate_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG_PATH = REPO_ROOT / "config" / "demo.json"


def test_committed_demo_config_matches_the_built_in_default() -> None:
    committed = json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))

    assert committed == DEFAULT_CONFIG_MAPPING


def test_run_demo_succeeds_and_writes_the_documented_artifacts(tmp_path) -> None:
    output = tmp_path / "demo"

    status = main(["run-demo", "--output-dir", str(output)])

    assert status == 0
    for relative in [*ARTIFACT_PATHS.values(), MANIFEST_NAME]:
        assert (output / relative).is_file()
    validate_manifest(output)


def test_seed_option_overrides_the_configured_seed(tmp_path) -> None:
    output = tmp_path / "demo"

    main(["run-demo", "--output-dir", str(output), "--seed", "1234"])

    assert read_manifest(output / MANIFEST_NAME)["seed"] == 1234


def test_documented_command_line_from_the_readme_runs(tmp_path) -> None:
    output = tmp_path / "ci-demo"

    status = main(["run-demo", "--output-dir", str(output), "--seed", "20260807"])

    assert status == 0
    assert read_manifest(output / MANIFEST_NAME)["seed"] == 20260807


def test_explicit_config_file_is_honoured(tmp_path) -> None:
    custom = tmp_path / "custom.json"
    mapping = json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))
    mapping["seed"] = 7
    custom.write_text(json.dumps(mapping), encoding="utf-8")
    output = tmp_path / "demo"

    main(["run-demo", "--output-dir", str(output), "--config", str(custom)])

    assert read_manifest(output / MANIFEST_NAME)["seed"] == 7


def test_missing_config_file_fails_closed_with_status_one(tmp_path, capsys) -> None:
    status = main(
        ["run-demo", "--output-dir", str(tmp_path / "demo"), "--config", str(tmp_path / "no.json")]
    )

    assert status == 1
    assert "does not exist" in capsys.readouterr().err


def test_malformed_config_fails_closed_with_status_one(tmp_path, capsys) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema_version": 1}', encoding="utf-8")

    status = main(["run-demo", "--output-dir", str(tmp_path / "demo"), "--config", str(bad)])

    assert status == 1
    assert "missing" in capsys.readouterr().err


def test_negative_seed_fails_closed_with_status_one(tmp_path, capsys) -> None:
    status = main(["run-demo", "--output-dir", str(tmp_path / "demo"), "--seed", "-5"])

    assert status == 1
    assert "negative" in capsys.readouterr().err


def test_missing_output_dir_argument_is_a_usage_error(tmp_path) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["run-demo"])

    assert raised.value.code == 2


def test_unknown_subcommand_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as raised:
        main(["rotation-curve"])

    assert raised.value.code == 2


def test_no_subcommand_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as raised:
        main([])

    assert raised.value.code == 2


def test_version_flag_reports_the_package_version(capsys) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--version"])

    assert raised.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_run_demo_reports_the_synthetic_boundary_on_stdout(tmp_path, capsys) -> None:
    main(["run-demo", "--output-dir", str(tmp_path / "demo")])

    out = capsys.readouterr().out.lower()
    assert "synthetic" in out
    assert "not an observation" in out
