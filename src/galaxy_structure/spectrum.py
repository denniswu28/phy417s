"""The two-column synthetic spectrum type, its schema contract, and its file format.

The schema mirrors the shape recorded for the historical measured files in the
accepted audit of the control repository -- two columns with a unit-declaring
header, strictly increasing frequency on a uniform grid. No measured file is
read, shipped, or reproduced by this package: every spectrum handled here is
synthetic and is labelled as such both in memory and on disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .errors import SpectrumSchemaError

#: Only synthetic data is representable. The label is part of the schema so that
#: an artifact can never silently lose its synthetic provenance.
SYNTHETIC_LABEL = "synthetic"

#: A spectrum needs at least two channels for a channel width to be defined.
MIN_CHANNELS = 2

#: Relative tolerance used when asserting that a frequency grid is uniform.
GRID_UNIFORMITY_RTOL = 1e-9

FREQUENCY_UNIT_LABEL = "Frequency, Hz"
AMPLITUDE_UNIT_LABEL = "Amplitude, Volts"

_COLUMN_SEPARATOR = "\t"


def _as_one_dimensional(values: np.ndarray, name: str) -> np.ndarray:
    # Always copy: the stored arrays are frozen read-only, and freezing an array
    # the caller still owns would be a surprising side effect.
    array = np.array(values, dtype=np.float64, copy=True)
    if array.ndim != 1:
        raise SpectrumSchemaError(
            f"{name} must be one-dimensional; got an array with {array.ndim} dimensions."
        )
    return array


@dataclass(frozen=True)
class Spectrum:
    """An immutable, unit-explicit, synthetic two-column spectrum.

    Attributes:
        frequency_hz: Channel frequencies in hertz -- strictly increasing,
            finite, positive, and uniformly spaced.
        amplitude_volts: Channel amplitudes in volts -- finite, and the same
            length as ``frequency_hz``.
        label: Always ``"synthetic"``; any other value is rejected.
    """

    frequency_hz: np.ndarray
    amplitude_volts: np.ndarray
    label: str = field(default=SYNTHETIC_LABEL)

    def __post_init__(self) -> None:
        if self.label != SYNTHETIC_LABEL:
            raise SpectrumSchemaError(
                f"label must be {SYNTHETIC_LABEL!r}; this package represents no measured "
                f"observation, and {self.label!r} was supplied."
            )

        frequency = _as_one_dimensional(self.frequency_hz, "frequency_hz")
        amplitude = _as_one_dimensional(self.amplitude_volts, "amplitude_volts")

        if frequency.size != amplitude.size:
            raise SpectrumSchemaError(
                "frequency_hz and amplitude_volts must have the same length; got "
                f"{frequency.size} and {amplitude.size}."
            )
        if frequency.size < MIN_CHANNELS:
            raise SpectrumSchemaError(
                f"a spectrum needs at least {MIN_CHANNELS} channels; got {frequency.size}."
            )
        if not np.isfinite(frequency).all():
            raise SpectrumSchemaError("frequency_hz contains non-finite values (NaN or infinity).")
        if not np.isfinite(amplitude).all():
            raise SpectrumSchemaError(
                "amplitude_volts contains non-finite values (NaN or infinity)."
            )
        if not bool((frequency > 0.0).all()):
            raise SpectrumSchemaError("frequency_hz must be strictly positive.")

        spacing = np.diff(frequency)
        if not bool((spacing > 0.0).all()):
            raise SpectrumSchemaError(
                "frequency_hz must be strictly increasing; duplicated or descending "
                "frequencies are rejected rather than sorted silently."
            )
        width = float(np.median(spacing))
        if not bool(np.allclose(spacing, width, rtol=GRID_UNIFORMITY_RTOL, atol=0.0)):
            raise SpectrumSchemaError(
                "frequency_hz must lie on a uniform grid; the channel spacing varies by more "
                f"than a relative {GRID_UNIFORMITY_RTOL:g}."
            )

        frequency.setflags(write=False)
        amplitude.setflags(write=False)
        object.__setattr__(self, "frequency_hz", frequency)
        object.__setattr__(self, "amplitude_volts", amplitude)

    @property
    def n_channels(self) -> int:
        """Number of frequency channels."""
        return int(self.frequency_hz.size)

    @property
    def channel_width_hz(self) -> float:
        """Uniform channel spacing in hertz."""
        return float(np.median(np.diff(self.frequency_hz)))

    def with_amplitude(self, amplitude_volts: np.ndarray) -> Spectrum:
        """Return a new spectrum sharing this frequency grid with new amplitudes."""
        return Spectrum(frequency_hz=self.frequency_hz.copy(), amplitude_volts=amplitude_volts)


def _format(value: float) -> str:
    # repr is the shortest representation that round-trips a float64 exactly,
    # which keeps written artifacts both exact and byte-stable.
    return repr(float(value))


def write_spectrum(spectrum: Spectrum, path: Path) -> None:
    """Write ``spectrum`` as a two-column, unit-labelled, synthetic ``.dat`` file.

    The output is byte-identical for equal input: no timestamp, host name, user
    name, or absolute path is written.
    """
    path = Path(path)
    lines = [
        f"# {SYNTHETIC_LABEL} spectrum generated by galaxy-structure; not an observation.",
        f"# {FREQUENCY_UNIT_LABEL}{_COLUMN_SEPARATOR}{AMPLITUDE_UNIT_LABEL}",
    ]
    lines.extend(
        f"{_format(frequency)}{_COLUMN_SEPARATOR}{_format(amplitude)}"
        for frequency, amplitude in zip(
            spectrum.frequency_hz, spectrum.amplitude_volts, strict=True
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def read_spectrum(path: Path) -> Spectrum:
    """Read a two-column, unit-labelled, synthetic ``.dat`` file written by this package."""
    path = Path(path)
    if not path.is_file():
        raise SpectrumSchemaError(f"spectrum file does not exist: {path.name}")

    text = path.read_text(encoding="utf-8")
    comments = [line for line in text.splitlines() if line.lstrip().startswith("#")]
    data_lines = [
        line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
    ]

    if not any(FREQUENCY_UNIT_LABEL in line and AMPLITUDE_UNIT_LABEL in line for line in comments):
        raise SpectrumSchemaError(
            "missing unit header; expected a comment line declaring "
            f"{FREQUENCY_UNIT_LABEL!r} and {AMPLITUDE_UNIT_LABEL!r} in {path.name}."
        )
    if not any(SYNTHETIC_LABEL in line.lower() for line in comments):
        raise SpectrumSchemaError(
            f"missing {SYNTHETIC_LABEL!r} label in the header of {path.name}; this package "
            "reads only spectra that it generated and labelled synthetic."
        )

    rows = [line.split() for line in data_lines]
    if any(len(row) != 2 for row in rows):
        raise SpectrumSchemaError(
            f"expected exactly two columns per data row in {path.name}; found a row with a "
            "different column count."
        )

    values = np.array(rows, dtype=np.float64)
    return Spectrum(frequency_hz=values[:, 0], amplitude_volts=values[:, 1])
