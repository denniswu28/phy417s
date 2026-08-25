"""The end-to-end synthetic demo run, its exact artifact set, and its manifest."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from galaxy_structure.config import load_config
from galaxy_structure.demo import ARTIFACT_PATHS, MANIFEST_NAME, run_demo
from galaxy_structure.errors import ManifestError
from galaxy_structure.manifest import read_manifest, validate_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG_PATH = REPO_ROOT / "config" / "demo.json"

# A drive letter must not be preceded by another letter, so that a URL scheme
# such as "https:" is not mistaken for "C:".
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:(?<![A-Za-z])[A-Za-z]:[\\/])|(?:/home/)|(?:/Users/)|(?:\\\\)"
)

#: A distinctive directory name, so a leaked output path is unmistakable.
OUTPUT_DIR_MARKER = "gs-output-dir-marker"


@pytest.fixture
def config():
    return load_config(DEMO_CONFIG_PATH)


@pytest.fixture
def run(config, tmp_path):
    return run_demo(config, tmp_path / OUTPUT_DIR_MARKER)


def test_run_produces_exactly_the_documented_artifact_set(run) -> None:
    produced = sorted(
        p.relative_to(run.output_dir).as_posix() for p in run.output_dir.rglob("*") if p.is_file()
    )

    assert produced == sorted([*ARTIFACT_PATHS.values(), MANIFEST_NAME])


def test_every_artifact_is_non_empty(run) -> None:
    for relative in [*ARTIFACT_PATHS.values(), MANIFEST_NAME]:
        assert (run.output_dir / relative).stat().st_size > 0


def test_manifest_validates_against_the_files_on_disk(run) -> None:
    validate_manifest(run.output_dir)


def test_manifest_records_a_hash_and_synthetic_label_for_every_artifact(run) -> None:
    manifest = read_manifest(run.output_dir / MANIFEST_NAME)

    recorded = {entry["path"] for entry in manifest["artifacts"]}
    assert recorded == set(ARTIFACT_PATHS.values())
    for entry in manifest["artifacts"]:
        assert entry["label"] == "synthetic"
        assert len(entry["sha256"]) == 64
        assert entry["bytes"] > 0


def test_manifest_records_seed_configuration_versions_and_command_template(run, config) -> None:
    manifest = read_manifest(run.output_dir / MANIFEST_NAME)

    assert manifest["seed"] == config.seed
    assert manifest["configuration"] == config.to_mapping()
    assert len(manifest["configuration_checksum"]) == 64
    assert manifest["command_template"] == (
        "galaxy-structure run-demo --output-dir OUTPUT_DIR --seed SEED"
    )
    for package in ("galaxy-structure", "numpy", "astropy", "matplotlib", "python"):
        assert manifest["package_versions"][package]


def test_manifest_records_the_reference_frame_boundary(run) -> None:
    manifest = read_manifest(run.output_dir / MANIFEST_NAME)

    assert manifest["reference_frame"] == "none-applied"
    assert manifest["label"] == "synthetic"
    assert any("rotation curve" in line.lower() for line in manifest["boundaries"])


def test_no_artifact_contains_an_absolute_runtime_path(run) -> None:
    for relative in [*ARTIFACT_PATHS.values(), MANIFEST_NAME]:
        path = run.output_dir / relative
        if path.suffix == ".png":
            continue
        text = path.read_text(encoding="utf-8")
        assert OUTPUT_DIR_MARKER not in text, f"output directory leaked into {relative}"
        assert not ABSOLUTE_PATH_PATTERN.search(text), f"absolute path leaked into {relative}"


def test_manifest_does_not_name_the_output_directory(run) -> None:
    text = (run.output_dir / MANIFEST_NAME).read_text(encoding="utf-8")

    assert OUTPUT_DIR_MARKER not in text
    assert str(run.output_dir) not in text


def test_two_runs_in_separate_directories_are_byte_identical(config, tmp_path) -> None:
    first = run_demo(config, tmp_path / "one")
    second = run_demo(config, tmp_path / "two")

    for relative in [*ARTIFACT_PATHS.values(), MANIFEST_NAME]:
        assert (first.output_dir / relative).read_bytes() == (
            second.output_dir / relative
        ).read_bytes(), f"{relative} is not reproducible"


def test_a_different_seed_changes_the_generated_spectrum(config, tmp_path) -> None:
    first = run_demo(config, tmp_path / "one")
    second = run_demo(config.with_seed(config.seed + 1), tmp_path / "two")

    spectrum = ARTIFACT_PATHS["spectrum"]
    assert (first.output_dir / spectrum).read_bytes() != (second.output_dir / spectrum).read_bytes()


def test_validate_manifest_detects_a_modified_artifact(run) -> None:
    target = run.output_dir / ARTIFACT_PATHS["spectrum"]
    target.write_text(target.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")

    with pytest.raises(ManifestError, match="checksum"):
        validate_manifest(run.output_dir)


def test_validate_manifest_detects_a_missing_artifact(run) -> None:
    (run.output_dir / ARTIFACT_PATHS["velocity_table"]).unlink()

    with pytest.raises(ManifestError, match="missing"):
        validate_manifest(run.output_dir)


def test_validate_manifest_detects_an_unexpected_extra_file(run) -> None:
    (run.output_dir / "unexpected.txt").write_text("extra", encoding="utf-8")

    with pytest.raises(ManifestError, match="unexpected"):
        validate_manifest(run.output_dir)


def test_validate_manifest_rejects_a_missing_manifest(tmp_path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    with pytest.raises(ManifestError, match="does not exist"):
        validate_manifest(empty)


def test_run_fails_closed_when_the_output_path_is_a_file(config, tmp_path) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")

    with pytest.raises(OSError):
        run_demo(config, blocker)


def test_run_result_exposes_the_figure_records(run) -> None:
    claim_ids = [record.claim_id for record in run.figures]

    assert claim_ids == ["GS-FIG-001", "GS-FIG-002"]


def test_manifest_is_sorted_and_canonically_formatted(run) -> None:
    text = (run.output_dir / MANIFEST_NAME).read_text(encoding="utf-8")
    manifest = json.loads(text)

    assert [entry["path"] for entry in manifest["artifacts"]] == sorted(
        entry["path"] for entry in manifest["artifacts"]
    )
    assert text.endswith("\n")
