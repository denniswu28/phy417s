"""Frequency-to-velocity conversion for the synthetic demonstration.

Scope boundary -- read this before using anything here.

The conversion below requires an explicit rest-frequency :class:`~astropy.units.Quantity`
and an explicit Doppler convention. Both are **synthetic-demonstration
conventions only**. They do not:

* answer owner-brief question 13,
* select the historically correct frequency scale or Doppler formula for the
  measured files that this repository does not ship,
* validate the legacy implementation described in the accepted audit, or
* authorise any real-observation scientific claim.

The default convention documented for this demo is Astropy's relativistic
Doppler equivalency:
https://docs.astropy.org/en/stable/api/astropy.units.doppler_relativistic.html

The default rest frequency is the recommended hydrogen ground-state hyperfine
transition frequency from the NIST hydrogen compilation, 1 420 405 751.768(1) Hz:
https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=842564

That is an external reference value, not a result produced by this project.

The velocity coordinate produced here has **no observational reference frame
applied**. It is not topocentric, geocentric, barycentric, heliocentric, or LSR.
Requests for those corrections fail closed in :mod:`galaxy_structure.unavailable`.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import astropy.units as u
import numpy as np

from .errors import UnitError
from .spectrum import SYNTHETIC_LABEL, Spectrum

#: Recommended hydrogen ground-state hyperfine transition frequency, in hertz,
#: as given by the cited NIST compilation: 1 420 405 751.768(1) Hz.
NIST_HYDROGEN_HYPERFINE_FREQUENCY_HZ = 1420405751.768

#: Primary documentation for the value above.
NIST_HYDROGEN_REFERENCE_URL = "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=842564"

#: Primary documentation for the default Doppler convention.
ASTROPY_DOPPLER_REFERENCE_URL = (
    "https://docs.astropy.org/en/stable/api/astropy.units.doppler_relativistic.html"
)

#: Documented tolerance for a frequency -> velocity -> frequency round trip.
ROUND_TRIP_RTOL = 1e-12

#: Recorded in every velocity artifact: no observational frame correction is applied.
NO_REFERENCE_FRAME = "none-applied"

_EQUIVALENCIES = {
    "relativistic": u.doppler_relativistic,
    "radio": u.doppler_radio,
    "optical": u.doppler_optical,
}

#: Doppler conventions this package accepts, in a stable documented order.
SUPPORTED_CONVENTIONS = tuple(_EQUIVALENCIES)

_VELOCITY_UNIT = u.km / u.s


def _require_quantity(value: object, name: str) -> u.Quantity:
    if not isinstance(value, u.Quantity):
        raise UnitError(
            f"{name} must be an astropy Quantity carrying an explicit unit; got "
            f"{type(value).__name__}. A bare number is rejected because the audited legacy "
            "code carried two different rest-frequency scales for the same symbol."
        )
    return value


def _require_frequency(value: object, name: str) -> u.Quantity:
    quantity = _require_quantity(value, name)
    if not quantity.unit.is_equivalent(u.Hz):
        raise UnitError(f"{name} must have a frequency unit; got {quantity.unit!s}.")
    if not bool(np.isfinite(quantity.to_value(u.Hz)).all()):
        raise UnitError(f"{name} contains non-finite values (NaN or infinity).")
    return quantity


def _resolve(rest_frequency: object, convention: str) -> tuple[u.Quantity, object]:
    rest = _require_frequency(rest_frequency, "rest_frequency")
    if not rest.isscalar:
        raise UnitError("rest_frequency must be a scalar quantity, not an array.")
    if rest.to_value(u.Hz) <= 0.0:
        raise UnitError("rest_frequency must be strictly positive.")
    if convention not in _EQUIVALENCIES:
        raise UnitError(
            f"unknown Doppler convention {convention!r}; supported conventions are "
            f"{', '.join(SUPPORTED_CONVENTIONS)}. The convention is never inferred."
        )
    return rest, _EQUIVALENCIES[convention](rest)


def frequency_to_velocity(
    frequency: object, *, rest_frequency: object, convention: str
) -> u.Quantity:
    """Convert frequency to radial velocity in km/s under an explicit convention.

    Args:
        frequency: Frequency quantity with an explicit frequency unit.
        rest_frequency: Scalar, strictly positive rest-frequency quantity.
        convention: One of :data:`SUPPORTED_CONVENTIONS`. Never inferred.

    Returns:
        Radial velocity as a quantity in km/s, with **no** reference-frame
        correction applied.
    """
    _, equivalency = _resolve(rest_frequency, convention)
    value = _require_frequency(frequency, "frequency")
    return value.to(_VELOCITY_UNIT, equivalencies=equivalency)


def velocity_to_frequency(
    velocity: object, *, rest_frequency: object, convention: str
) -> u.Quantity:
    """Convert radial velocity back to frequency in hertz under an explicit convention."""
    _, equivalency = _resolve(rest_frequency, convention)
    value = _require_quantity(velocity, "velocity")
    if not value.unit.is_equivalent(_VELOCITY_UNIT):
        raise UnitError(f"velocity must have a speed unit; got {value.unit!s}.")
    if not bool(np.isfinite(value.to_value(_VELOCITY_UNIT)).all()):
        raise UnitError("velocity contains non-finite values (NaN or infinity).")
    return value.to(u.Hz, equivalencies=equivalency)


@dataclass(frozen=True)
class VelocityTable:
    """A synthetic frequency/velocity/amplitude table with its conversion metadata."""

    frequency_hz: np.ndarray
    velocity_km_s: np.ndarray
    amplitude_volts: np.ndarray
    rest_frequency_hz: float
    convention: str
    frequency_unit: str = "Hz"
    velocity_unit: str = "km / s"
    amplitude_unit: str = "Volts"
    reference_frame: str = NO_REFERENCE_FRAME
    label: str = SYNTHETIC_LABEL

    def write(self, path: Path) -> None:
        """Write the table as a deterministic, labelled CSV file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        header = [
            f"# {SYNTHETIC_LABEL} velocity table generated by galaxy-structure; "
            "not an observation.",
            f"# rest_frequency_hz: {self.rest_frequency_hz!r} "
            f"(NIST recommended value, {NIST_HYDROGEN_REFERENCE_URL})",
            f"# doppler_convention: {self.convention} ({ASTROPY_DOPPLER_REFERENCE_URL})",
            f"# reference_frame: {self.reference_frame} "
            "(no barycentric, heliocentric, or LSR correction is applied)",
        ]
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for line in header:
                handle.write(line + "\n")
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(["frequency_hz", "velocity_km_s", "amplitude_volts"])
            for frequency, velocity, amplitude in zip(
                self.frequency_hz, self.velocity_km_s, self.amplitude_volts, strict=True
            ):
                writer.writerow(
                    [repr(float(frequency)), repr(float(velocity)), repr(float(amplitude))]
                )


def velocity_table(spectrum: Spectrum, *, rest_frequency: object, convention: str) -> VelocityTable:
    """Build a velocity table for ``spectrum`` under an explicit rest frequency and convention."""
    rest, _ = _resolve(rest_frequency, convention)
    velocity = frequency_to_velocity(
        spectrum.frequency_hz * u.Hz, rest_frequency=rest, convention=convention
    )
    return VelocityTable(
        frequency_hz=spectrum.frequency_hz,
        velocity_km_s=velocity.to_value(_VELOCITY_UNIT),
        amplitude_volts=spectrum.amplitude_volts,
        rest_frequency_hz=float(rest.to_value(u.Hz)),
        convention=convention,
    )
