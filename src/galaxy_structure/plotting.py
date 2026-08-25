"""Deterministic figure rendering.

Every figure produced here is a **synthetic demonstration**. Each carries a
conspicuous label, a stable claim ID registered in ``docs/claim-evidence.md``,
explicit axis units, and an explicit statement that no observational reference
frame was applied.

Determinism: the non-interactive Agg backend is used, the figure size, DPI,
style, and fonts are fixed, the plotting order is fixed, and the PNG's
``Software`` metadata entry is removed so that no library version, creation
time, host name, user name, or absolute path can reach the committed bytes. The
matplotlib version is pinned in ``constraints-ci.txt``; byte-identity is claimed
only within that pinned environment.

Figures are committed as PNG only -- never PDF or SVG, both of which embed
producer and creation metadata by default.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from .interference import CleaningResult
from .spectrum import SYNTHETIC_LABEL, Spectrum
from .velocity import (
    ASTROPY_DOPPLER_REFERENCE_URL,
    NO_REFERENCE_FRAME,
    VelocityTable,
)

#: Conspicuous label carried by every figure and every caption.
SYNTHETIC_FIGURE_LABEL = "Synthetic demonstration"

#: Stable claim IDs, registered in docs/claim-evidence.md.
BEFORE_AFTER_CLAIM_ID = "GS-FIG-001"
VELOCITY_MAPPING_CLAIM_ID = "GS-FIG-002"

#: Fixed rendering parameters. Changing any of these changes the committed bytes.
FIGURE_SIZE_INCHES = (9.0, 5.0)
FIGURE_DPI = 120

_RC_PARAMS = {
    "figure.dpi": FIGURE_DPI,
    "savefig.dpi": FIGURE_DPI,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 10.0,
    "axes.titlesize": 11.0,
    "axes.labelsize": 10.0,
    "legend.fontsize": 9.0,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "lines.linewidth": 1.0,
    "savefig.bbox": "standard",
    "svg.hashsalt": "galaxy-structure",
    "path.simplify": False,
}

# Removing the Software entry keeps the matplotlib version out of the bytes; no
# other metadata is written by the Agg PNG writer.
_PNG_METADATA: dict[str, None] = {"Software": None}


@dataclass(frozen=True)
class FigureRecord:
    """Provenance for one committed figure."""

    filename: str
    claim_id: str
    caption: str
    x_axis_unit: str
    y_axis_unit: str
    label: str
    reference_frame: str

    def to_mapping(self) -> dict[str, str]:
        """Return the record as a plain, JSON-serialisable mapping of strings."""
        return {key: str(value) for key, value in asdict(self).items()}


def _new_figure() -> Figure:
    figure = Figure(figsize=FIGURE_SIZE_INCHES, dpi=FIGURE_DPI, layout="constrained")
    FigureCanvasAgg(figure)
    return figure


def _save(figure: Figure, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, format="png", dpi=FIGURE_DPI, metadata=_PNG_METADATA)


def _banner(figure: Figure, text: str) -> None:
    figure.suptitle(f"{SYNTHETIC_FIGURE_LABEL} - {text}", fontweight="bold")


def plot_before_after(
    *, original: Spectrum, injected: Spectrum, cleaned: CleaningResult, path: Path
) -> FigureRecord:
    """Render the before/after synthetic-spectrum figure and return its provenance."""
    with matplotlib.rc_context(_RC_PARAMS):
        figure = _new_figure()
        axes = figure.subplots(2, 1, sharex=True)

        axes[0].plot(
            original.frequency_hz, original.amplitude_volts, label="synthetic spectrum", zorder=1
        )
        axes[0].plot(
            injected.frequency_hz,
            injected.amplitude_volts,
            label="with synthetic interference",
            zorder=2,
        )
        axes[0].set_ylabel("Amplitude, Volts")
        axes[0].legend(loc="upper right")
        axes[0].set_title("Before cleaning")

        axes[1].plot(
            cleaned.spectrum.frequency_hz,
            cleaned.spectrum.amplitude_volts,
            label="cleaned synthetic spectrum",
            zorder=1,
        )
        masked = np.flatnonzero(cleaned.mask)
        if masked.size:
            axes[1].plot(
                cleaned.spectrum.frequency_hz[masked],
                cleaned.spectrum.amplitude_volts[masked],
                linestyle="none",
                marker="o",
                markersize=3.0,
                label=f"masked channels (n={masked.size})",
                zorder=2,
            )
        axes[1].set_xlabel("Frequency, Hz")
        axes[1].set_ylabel("Amplitude, Volts")
        axes[1].legend(loc="upper right")
        axes[1].set_title("After cleaning")

        caption = (
            f"{SYNTHETIC_FIGURE_LABEL} ({BEFORE_AFTER_CLAIM_ID}). Synthetic spectrum before and "
            "after deterministic removal of synthetic interference that this package injected. "
            "Not an observation; no measured data is involved, and no interference-removal "
            "performance on real observations is claimed."
        )
        _banner(figure, "synthetic spectrum before and after cleaning")
        figure.supxlabel(caption, fontsize=7.5, wrap=True)
        _save(figure, path)

    return FigureRecord(
        filename=Path(path).name,
        claim_id=BEFORE_AFTER_CLAIM_ID,
        caption=caption,
        x_axis_unit="Hz",
        y_axis_unit="Volts",
        label=SYNTHETIC_LABEL,
        reference_frame=NO_REFERENCE_FRAME,
    )


def plot_frequency_velocity(*, table: VelocityTable, path: Path) -> FigureRecord:
    """Render the synthetic frequency/velocity mapping figure and return its provenance."""
    with matplotlib.rc_context(_RC_PARAMS):
        figure = _new_figure()
        axes = figure.subplots(1, 1)

        axes.plot(table.frequency_hz, table.velocity_km_s, zorder=1)
        axes.axvline(table.rest_frequency_hz, linestyle="--", linewidth=0.8, zorder=2)
        axes.axhline(0.0, linestyle=":", linewidth=0.8, zorder=3)
        axes.set_xlabel(f"Frequency, {table.frequency_unit}")
        axes.set_ylabel(f"Radial velocity, {table.velocity_unit}")
        axes.set_title(
            f"{table.convention} Doppler convention; rest frequency "
            f"{table.rest_frequency_hz!r} Hz; reference frame: {table.reference_frame}"
        )

        caption = (
            f"{SYNTHETIC_FIGURE_LABEL} ({VELOCITY_MAPPING_CLAIM_ID}). Frequency-to-velocity "
            f"mapping under the {table.convention} Doppler convention "
            f"({ASTROPY_DOPPLER_REFERENCE_URL}) and an explicit rest frequency. No "
            "observational reference-frame correction is applied: the velocity coordinate is "
            "not topocentric, geocentric, barycentric, heliocentric, or LSR. This is a "
            "software convention for a synthetic demonstration, not a validated method for "
            "any measurement."
        )
        _banner(figure, "synthetic frequency-to-velocity mapping")
        figure.supxlabel(caption, fontsize=7.5, wrap=True)
        _save(figure, path)

    return FigureRecord(
        filename=Path(path).name,
        claim_id=VELOCITY_MAPPING_CLAIM_ID,
        caption=caption,
        x_axis_unit=table.frequency_unit,
        y_axis_unit=table.velocity_unit,
        label=SYNTHETIC_LABEL,
        reference_frame=table.reference_frame,
    )
