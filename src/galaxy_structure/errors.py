"""Exception hierarchy.

Every failure in this package is explicit. No stage substitutes a default for a
missing input, returns a partial result, or silently coerces units.
"""

from __future__ import annotations


class GalaxyStructureError(Exception):
    """Base class for every error raised by this package."""


class ConfigurationError(GalaxyStructureError):
    """The demo configuration is missing, malformed, or out of range."""


class SpectrumSchemaError(GalaxyStructureError):
    """A spectrum violates the two-column unit-labelled schema contract."""


class UnitError(GalaxyStructureError):
    """A quantity carries missing, ambiguous, or incompatible units."""


class InterferenceError(GalaxyStructureError):
    """Synthetic interference injection or cleaning received invalid input."""


class ManifestError(GalaxyStructureError):
    """A run manifest is malformed or does not describe the artifacts on disk."""


class UnavailableStageError(GalaxyStructureError):
    """A named stage is unavailable because required evidence or input is absent.

    This package deliberately implements no real-observation calibration,
    reference-frame correction, galactic-geometry, or rotation-curve stage. The
    owner brief supplies no receiver, site, epoch, pointing-frame, calibration,
    or reference-method evidence for the historical measurements, so those
    stages fail closed rather than returning a stubbed or zero result.
    """
