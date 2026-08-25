"""The end-to-end synthetic demonstration run.

The run generates a synthetic spectrum, injects deterministic synthetic
interference, cleans it while recording an explicit mask, converts frequency to
a velocity coordinate under an explicit convention, renders two labelled
figures, and writes a manifest describing everything it produced.

It produces no rotation curve, labels nothing as an observation, and writes no
absolute runtime path into any artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import DemoConfig
from .interference import clean_interference, inject_interference
from .manifest import build_manifest, write_manifest
from .plotting import FigureRecord, plot_before_after, plot_frequency_velocity
from .spectrum import Spectrum, write_spectrum
from .synthetic import generate_spectrum
from .velocity import VelocityTable, velocity_table

#: Name of the run manifest inside the output directory.
MANIFEST_NAME = "manifest.json"

#: The exact artifact set a run produces, as output-relative POSIX paths.
ARTIFACT_PATHS = {
    "spectrum": "synthetic_spectrum.dat",
    "spectrum_with_interference": "synthetic_spectrum_with_interference.dat",
    "spectrum_cleaned": "synthetic_spectrum_cleaned.dat",
    "interference_mask": "synthetic_interference_mask.csv",
    "velocity_table": "synthetic_velocity_table.csv",
    "figure_before_after": "figures/synthetic_spectrum_before_after.png",
    "figure_frequency_velocity": "figures/synthetic_frequency_velocity_mapping.png",
}

#: One-line description recorded in the manifest for each artifact.
ARTIFACT_DESCRIPTIONS = {
    "spectrum": "Synthetic spectrum on a strictly increasing, uniform frequency grid.",
    "spectrum_with_interference": (
        "The same synthetic spectrum with deterministic synthetic narrow-band interference."
    ),
    "spectrum_cleaned": "The synthetic spectrum after deterministic interference masking.",
    "interference_mask": "Explicit record of every synthetic sample the cleaner altered.",
    "velocity_table": (
        "Synthetic velocity coordinate under an explicit rest frequency and Doppler "
        "convention, with no observational reference-frame correction applied."
    ),
    "figure_before_after": "Synthetic spectrum before and after cleaning (PNG).",
    "figure_frequency_velocity": "Synthetic frequency-to-velocity mapping (PNG).",
}


@dataclass(frozen=True)
class DemoRun:
    """Everything one demo run produced."""

    output_dir: Path
    config: DemoConfig
    spectrum: Spectrum
    injected: Spectrum
    cleaned: Spectrum
    table: VelocityTable
    figures: tuple[FigureRecord, ...]
    manifest: dict


def run_demo(config: DemoConfig, output_dir: Path) -> DemoRun:
    """Run the deterministic synthetic demo and write its artifacts to ``output_dir``."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    spectrum = generate_spectrum(config)
    injection = inject_interference(spectrum, config.interference)
    cleaning = clean_interference(injection.spectrum, config.cleaning)
    table = velocity_table(
        cleaning.spectrum,
        rest_frequency=config.velocity.rest_frequency,
        convention=config.velocity.doppler_convention,
    )

    write_spectrum(spectrum, output_dir / ARTIFACT_PATHS["spectrum"])
    write_spectrum(injection.spectrum, output_dir / ARTIFACT_PATHS["spectrum_with_interference"])
    write_spectrum(cleaning.spectrum, output_dir / ARTIFACT_PATHS["spectrum_cleaned"])
    cleaning.write_mask(output_dir / ARTIFACT_PATHS["interference_mask"])
    table.write(output_dir / ARTIFACT_PATHS["velocity_table"])

    before_after = plot_before_after(
        original=spectrum,
        injected=injection.spectrum,
        cleaned=cleaning,
        path=output_dir / ARTIFACT_PATHS["figure_before_after"],
    )
    mapping = plot_frequency_velocity(
        table=table, path=output_dir / ARTIFACT_PATHS["figure_frequency_velocity"]
    )

    manifest = build_manifest(
        config=config,
        output_dir=output_dir,
        artifacts=ARTIFACT_PATHS,
        descriptions=ARTIFACT_DESCRIPTIONS,
    )
    write_manifest(manifest, output_dir / MANIFEST_NAME)

    return DemoRun(
        output_dir=output_dir,
        config=config,
        spectrum=spectrum,
        injected=injection.spectrum,
        cleaned=cleaning.spectrum,
        table=table,
        figures=(before_after, mapping),
        manifest=manifest,
    )
