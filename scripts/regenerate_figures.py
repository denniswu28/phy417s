"""Regenerate the committed figures in ``docs/figures/`` and their provenance record.

Usage::

    python scripts/regenerate_figures.py

The script runs the deterministic synthetic demo into a temporary directory,
copies the two PNG figures into ``docs/figures/``, and rewrites
``docs/figures/figure-provenance.json``.

Under the pinned environment in ``constraints-ci.txt`` the output is
byte-identical on every run, so ``git diff --exit-code -- docs/figures`` is the
drift gate. The provenance record deliberately contains no absolute path, host
name, user name, Python version, or timestamp, so it stays identical across
machines within the pinned environment.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

if __package__ is None and str(REPO_ROOT / "src") not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(REPO_ROOT / "src"))

from galaxy_structure import __version__  # noqa: E402
from galaxy_structure.config import config_checksum, load_config  # noqa: E402
from galaxy_structure.demo import ARTIFACT_PATHS, run_demo  # noqa: E402
from galaxy_structure.manifest import sha256_file  # noqa: E402

CONFIG_PATH = REPO_ROOT / "config" / "demo.json"
FIGURES_DIR = REPO_ROOT / "docs" / "figures"
PROVENANCE_PATH = FIGURES_DIR / "figure-provenance.json"

GENERATING_COMMAND = "python scripts/regenerate_figures.py"

#: Which run artifacts each committed figure is derived from.
FIGURE_INPUTS = {
    "figure_before_after": ("spectrum", "spectrum_with_interference", "spectrum_cleaned"),
    "figure_frequency_velocity": ("spectrum_cleaned", "velocity_table"),
}


def _input_checksum(inputs: dict[str, str]) -> str:
    canonical = json.dumps(inputs, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> int:
    """Regenerate the committed figures. Returns the process exit status."""
    config = load_config(CONFIG_PATH)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as workspace:
        run = run_demo(config, Path(workspace) / "figures-run")
        artifact_key_for = {Path(ARTIFACT_PATHS[key]).name: key for key in FIGURE_INPUTS}

        figures = []
        for figure_record in run.figures:
            key = artifact_key_for[figure_record.filename]
            source = run.output_dir / ARTIFACT_PATHS[key]
            destination = FIGURES_DIR / figure_record.filename
            shutil.copyfile(source, destination)

            inputs = {
                ARTIFACT_PATHS[name]: sha256_file(run.output_dir / ARTIFACT_PATHS[name])
                for name in FIGURE_INPUTS[key]
            }
            entry = figure_record.to_mapping()
            entry.update(
                {
                    "generating_command": GENERATING_COMMAND,
                    "code_version": __version__,
                    "configuration_checksum": config_checksum(config),
                    "configuration_path": "config/demo.json",
                    "inputs": inputs,
                    "input_checksum": _input_checksum(inputs),
                    "sha256": sha256_file(destination),
                    "bytes": destination.stat().st_size,
                }
            )
            figures.append(entry)

    provenance = {
        "provenance_version": 1,
        "label": "synthetic",
        "generating_command": GENERATING_COMMAND,
        "code_version": __version__,
        "configuration_checksum": config_checksum(config),
        "note": (
            "Every figure recorded here is a synthetic demonstration. None of them is an "
            "observation, none carries an observational reference frame, and none supports a "
            "rotation-curve, galactic-structure, calibration-accuracy, uncertainty, or "
            "detection claim."
        ),
        "figures": sorted(figures, key=lambda entry: entry["filename"]),
    }
    PROVENANCE_PATH.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"Regenerated {len(figures)} synthetic figure(s) in docs/figures/:")
    for entry in provenance["figures"]:
        print(f"  {entry['filename']}  {entry['claim_id']}  sha256={entry['sha256'][:12]}...")
    print(f"  {PROVENANCE_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
