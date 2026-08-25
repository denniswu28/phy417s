"""Stages that are deliberately unavailable, and fail closed when called.

This package implements no real-observation calibration, reference-frame
correction, galactic-geometry, or rotation-curve stage. Each of them needs
evidence that the owner brief does not supply -- receiver and site, observing
epoch, pointing frame and epoch, calibration procedure, amplitude meaning, and a
named reference method -- and each of those items is recorded as
``TODO(Dennis)`` / ``NEEDS_REVIEW`` in the accepted control records.

Rather than omit the names silently, the package exposes them and makes every
one raise :class:`~galaxy_structure.errors.UnavailableStageError` naming the
missing inputs. Nothing here returns a stubbed value, a zero correction, a
partial result, or ``None``.

Astropy documents that even a barycentric or heliocentric radial-velocity
correction requires observing time and observatory location:
https://docs.astropy.org/en/latest/api/astropy.coordinates.SkyCoord.html
"""

from __future__ import annotations

from typing import Any, NoReturn

from .errors import UnavailableStageError

_ASTROPY_SKYCOORD_URL = "https://docs.astropy.org/en/latest/api/astropy.coordinates.SkyCoord.html"

_SYNTHETIC_BOUNDARY = "This package is a synthetic demonstration and produces no scientific result."

#: Names of every stage that is present but unavailable.
UNAVAILABLE_STAGES = (
    "apply_calibration",
    "barycentric_correction",
    "heliocentric_correction",
    "lsr_correction",
    "earth_motion_correction",
    "galactic_radius",
    "rotation_curve",
)


def _fail(stage: str, missing: str, *, citation: str | None = None) -> NoReturn:
    message = (
        f"{stage} is unavailable and fails closed. Required input or evidence is absent: "
        f"{missing} Each of these is recorded as TODO(Dennis) / NEEDS_REVIEW in the accepted "
        f"owner brief and audit, so no default, zero correction, or stubbed value is "
        f"substituted. {_SYNTHETIC_BOUNDARY}"
    )
    if citation is not None:
        message = f"{message} See {citation}"
    raise UnavailableStageError(message)


def apply_calibration(spectrum: Any, calibration: Any = None) -> NoReturn:
    """Unavailable: no calibration procedure or calibrated reference is established."""
    _fail(
        "apply_calibration",
        "the calibration procedure, the meaning of the recorded amplitude, the receiver and "
        "site configuration, and any characterised calibration accuracy.",
    )


def barycentric_correction(velocity: Any, observation: Any = None) -> NoReturn:
    """Unavailable: no observing time, location, or pointing is established."""
    _fail(
        "barycentric_correction",
        "the observing epoch, the observatory location, and the pointing coordinate and its "
        "frame. Astropy requires time and location information for this correction.",
        citation=_ASTROPY_SKYCOORD_URL,
    )


def heliocentric_correction(velocity: Any, observation: Any = None) -> NoReturn:
    """Unavailable: no observing time, location, or pointing is established."""
    _fail(
        "heliocentric_correction",
        "the observing epoch, the observatory location, and the pointing coordinate and its "
        "frame. Astropy requires time and location information for this correction.",
        citation=_ASTROPY_SKYCOORD_URL,
    )


def lsr_correction(velocity: Any, observation: Any = None) -> NoReturn:
    """Unavailable: no solar-motion convention or pointing frame is established."""
    _fail(
        "lsr_correction",
        "the observing epoch, the observatory location, the pointing coordinate and its frame, "
        "and the adopted solar-motion convention.",
    )


def earth_motion_correction(velocity: Any, observation: Any = None) -> NoReturn:
    """Unavailable: no observing epoch or observatory location is established."""
    _fail(
        "earth_motion_correction",
        "the observing epoch and the observatory location, without which no component of "
        "Earth's motion can be projected onto a line of sight.",
    )


def galactic_radius(velocity: Any, longitude: Any = None) -> NoReturn:
    """Unavailable: no validated pointing frame or geometry convention is established."""
    _fail(
        "galactic_radius",
        "a validated galactic-longitude value with its frame and epoch, a corrected "
        "reference-frame velocity, and the adopted solar radius and circular-speed "
        "convention. The longitude labels in the historical filenames are a naming "
        "convention only.",
    )


def rotation_curve(velocities: Any, radii: Any = None) -> NoReturn:
    """Unavailable: this project asserts no rotation curve and no scientific result."""
    _fail(
        "rotation_curve",
        "every input of galactic_radius, plus a named reference method against which a "
        "rebuilt pipeline could be validated. No rotation curve, rotation velocity, curve "
        "shape, or fit is produced, plotted, or claimed anywhere in this repository.",
    )
