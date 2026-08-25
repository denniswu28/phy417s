"""Packaging: wheel contents, declared metadata, and the console entry point.

The full fresh-environment build/install gate is the documented command sequence
in ``README.md``, which ``.github/workflows/ci.yml`` runs at the exact head.
These tests check the wheel that sequence builds, so a metadata or content
regression fails fast and locally.
"""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from importlib.metadata import entry_points, metadata
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

#: File types that must never be packaged: measured data, archives, notebooks,
#: spreadsheets, photographs, and generated binaries.
EXCLUDED_SUFFIXES = {
    ".dat",
    ".zip",
    ".fig",
    ".mat",
    ".xlsx",
    ".ipynb",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".csv",
    ".m",
}


@pytest.fixture(scope="module")
def wheel(tmp_path_factory) -> Path:
    """Build a wheel with the same backend the documented sequence uses."""
    pytest.importorskip("build", reason="the build front-end is pinned in constraints-ci.txt")

    outdir = tmp_path_factory.mktemp("dist")
    environment = {**os.environ, "PIP_CONSTRAINT": str(REPO_ROOT / "constraints-ci.txt")}
    completed = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir)],
        env=environment,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        pytest.fail(f"wheel build failed:\n{completed.stdout}\n{completed.stderr}")

    wheels = list(outdir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, got {wheels}"
    return wheels[0]


def test_wheel_declares_the_console_entry_point(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/entry_points.txt"))
        text = archive.read(name).decode("utf-8")

    assert "[console_scripts]" in text
    assert "galaxy-structure = galaxy_structure.cli:main" in text


def test_wheel_metadata_states_the_licence_and_python_requirement(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        text = archive.read(name).decode("utf-8")

    assert "License-Expression: GPL-3.0-or-later" in text
    assert "Requires-Python: >=3.12" in text
    assert "Name: galaxy-structure" in text


def test_wheel_includes_the_licence_file(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()

    assert any(n.endswith(".dist-info/licenses/LICENSE") or n.endswith("LICENSE") for n in names)


def test_wheel_contains_no_measured_data_or_legacy_artifact(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        suffixes = {Path(name).suffix.lower() for name in archive.namelist()}

    assert not (suffixes & EXCLUDED_SUFFIXES), f"wheel packages excluded file types: {suffixes}"


def test_wheel_ships_only_the_package_and_its_metadata(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        top_level = {name.split("/", 1)[0] for name in archive.namelist()}

    assert top_level == {"galaxy_structure", f"galaxy_structure-{_version()}.dist-info"}


def _version() -> str:
    from galaxy_structure import __version__

    return __version__


def test_installed_distribution_exposes_the_console_entry_point() -> None:
    scripts = entry_points(group="console_scripts")

    matching = [entry for entry in scripts if entry.name == "galaxy-structure"]

    assert matching, "the galaxy-structure console script is not registered"
    assert matching[0].value == "galaxy_structure.cli:main"


def test_installed_metadata_declares_the_licence() -> None:
    assert metadata("galaxy-structure")["License-Expression"] == "GPL-3.0-or-later"


def test_module_entry_point_runs_the_demo(tmp_path) -> None:
    output = tmp_path / "demo"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "galaxy_structure",
            "run-demo",
            "--output-dir",
            str(output),
            "--seed",
            "20260807",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "synthetic" in completed.stdout.lower()
    assert (output / "manifest.json").is_file()


def test_module_entry_point_reports_a_failure_with_a_non_zero_status(tmp_path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "galaxy_structure",
            "run-demo",
            "--output-dir",
            str(tmp_path / "demo"),
            "--config",
            str(tmp_path / "absent.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "does not exist" in completed.stderr
