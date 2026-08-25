"""Documentation integrity: claim registration, figure drift, and command parity.

These tests exist so that a public claim cannot appear without evidence, and so
that the documented commands cannot drift away from the ones CI runs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from galaxy_structure import __version__
from galaxy_structure.config import config_checksum, load_config
from galaxy_structure.manifest import sha256_file
from galaxy_structure.plotting import BEFORE_AFTER_CLAIM_ID, VELOCITY_MAPPING_CLAIM_ID

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
REGISTRY = DOCS / "claim-evidence.md"
FIGURES_DIR = DOCS / "figures"
FIGURE_PROVENANCE = FIGURES_DIR / "figure-provenance.json"

CLAIM_PATTERN = re.compile(r"GS-[A-Z]+-\d{3}")

#: Public documents whose claim IDs must all be registered.
PUBLIC_DOCUMENTS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "PROVENANCE.md",
    REPO_ROOT / "THIRD_PARTY_NOTICES.md",
    DOCS / "methodology.md",
    DOCS / "units-and-frames.md",
    DOCS / "limitations.md",
]

#: Every file the issue requires the repository surface to contain.
REQUIRED_SURFACE = [
    "README.md",
    "pyproject.toml",
    "constraints-ci.txt",
    "LICENSE",
    "PROVENANCE.md",
    "THIRD_PARTY_NOTICES.md",
    "CITATION.cff",
    "docs/claim-evidence.md",
    "docs/methodology.md",
    "docs/units-and-frames.md",
    "docs/limitations.md",
    "config/demo.json",
    "scripts/regenerate_figures.py",
    ".github/workflows/ci.yml",
]


def registered_claim_ids() -> set[str]:
    return set(CLAIM_PATTERN.findall(REGISTRY.read_text(encoding="utf-8")))


@pytest.mark.parametrize("relative", REQUIRED_SURFACE)
def test_required_repository_surface_is_present(relative: str) -> None:
    assert (REPO_ROOT / relative).is_file()


def test_required_directories_are_present() -> None:
    for relative in ("docs/figures", "src/galaxy_structure", "tests"):
        assert (REPO_ROOT / relative).is_dir()


@pytest.mark.parametrize("document", PUBLIC_DOCUMENTS, ids=lambda p: p.name)
def test_every_claim_id_in_a_public_document_is_registered(document: Path) -> None:
    registered = registered_claim_ids()

    used = set(CLAIM_PATTERN.findall(document.read_text(encoding="utf-8")))

    assert used <= registered, f"unregistered claim ID(s) in {document.name}: {used - registered}"


def test_figure_claim_ids_are_registered() -> None:
    registered = registered_claim_ids()

    assert BEFORE_AFTER_CLAIM_ID in registered
    assert VELOCITY_MAPPING_CLAIM_ID in registered


def test_registry_records_the_prohibited_claims() -> None:
    text = REGISTRY.read_text(encoding="utf-8")

    for claim_id in (
        "GS-ROTATION-001",
        "GS-GALSTRUCT-001",
        "GS-CALACC-001",
        "GS-UNCERT-001",
        "GS-DETECT-001",
    ):
        assert claim_id in text
    assert "NEEDS_REVIEW" in text


def test_no_public_document_claims_a_rotation_curve_result() -> None:
    forbidden = re.compile(
        r"\b(we (?:measured|detected|derived)|this project (?:measures|detects|derives))\b",
        re.IGNORECASE,
    )

    for document in PUBLIC_DOCUMENTS:
        assert not forbidden.search(document.read_text(encoding="utf-8")), document.name


def test_committed_figures_match_their_provenance_record() -> None:
    provenance = json.loads(FIGURE_PROVENANCE.read_text(encoding="utf-8"))

    for entry in provenance["figures"]:
        path = FIGURES_DIR / entry["filename"]
        assert path.is_file()
        assert sha256_file(path) == entry["sha256"]
        assert path.stat().st_size == entry["bytes"]


def test_figure_provenance_records_every_required_field() -> None:
    provenance = json.loads(FIGURE_PROVENANCE.read_text(encoding="utf-8"))

    assert provenance["code_version"] == __version__
    assert provenance["configuration_checksum"] == config_checksum(
        load_config(REPO_ROOT / "config" / "demo.json")
    )
    for entry in provenance["figures"]:
        for field in (
            "generating_command",
            "input_checksum",
            "inputs",
            "configuration_checksum",
            "code_version",
            "x_axis_unit",
            "y_axis_unit",
            "label",
            "reference_frame",
            "claim_id",
            "caption",
        ):
            assert entry[field], f"{entry['filename']} is missing {field}"
        assert entry["label"] == "synthetic"
        assert entry["reference_frame"] == "none-applied"
        assert "Synthetic demonstration" in entry["caption"]


def test_only_png_figures_are_committed() -> None:
    committed = {path.suffix for path in FIGURES_DIR.iterdir() if path.is_file()}

    assert committed <= {".png", ".json"}
    assert ".pdf" not in committed
    assert ".svg" not in committed


def test_readme_verification_block_matches_the_ci_workflow() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    documented = [
        "python -m pip install --constraint constraints-ci.txt build ruff pytest",
        "python -m build --wheel --outdir dist",
        "python -m pip install --constraint constraints-ci.txt dist/*.whl",
        "python -m pip check",
        "ruff check .",
        "ruff format --check .",
        "python -m pytest -q",
        "galaxy-structure run-demo --output-dir output/ci-demo --seed 20260807",
        "python scripts/regenerate_figures.py",
        "git diff --exit-code -- docs/figures",
    ]

    for command in documented:
        assert command in readme, f"README is missing the documented command: {command}"
        assert command in workflow, f"CI does not run the documented command: {command}"


def test_readme_states_the_synthetic_only_boundary() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()

    assert "synthetic" in readme
    assert "no measured observation" in readme
    assert "rotation-curve" in readme


def test_citation_file_declares_the_licence_and_no_fabricated_identifier() -> None:
    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")

    assert "cff-version: 1.2.0" in citation
    assert "license: GPL-3.0-or-later" in citation
    assert "doi:" not in citation.lower()


def test_third_party_notices_separate_the_historical_mit_fact() -> None:
    notices = (REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert "GPL-3.0-or-later" in notices
    assert "MIT" in notices
    assert "No legal or licence-compatibility conclusion" in notices


def test_provenance_records_the_source_commit_and_clean_room_boundary() -> None:
    provenance = (REPO_ROOT / "PROVENANCE.md").read_text(encoding="utf-8")

    assert "7faf67b306d6f5f0dad9c848ef1d5136a66c70f0" in provenance
    assert "denniswu28/phy417s" in provenance
    assert "No legacy code or notebook cell is retained" in provenance
    assert "retains no measured data" in provenance
