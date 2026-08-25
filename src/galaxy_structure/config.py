"""Demo configuration: parsing, strict validation, and a stable checksum.

Configuration is the only place a run is parameterised. Every key is required
and every unknown key is an error, so a stage can never silently fall back to a
default the operator did not write down.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import astropy.units as u

from .errors import ConfigurationError
from .spectrum import MIN_CHANNELS, SYNTHETIC_LABEL
from .velocity import SUPPORTED_CONVENTIONS

#: The only configuration schema this package understands.
SCHEMA_VERSION = 1

#: The built-in default configuration.
#:
#: ``config/demo.json`` in the repository is the documented, editable copy of
#: this mapping, and ``tests/test_cli.py`` asserts that the two never drift
#: apart. Keeping the default in code lets an installed wheel run the demo
#: without needing a checkout.
DEFAULT_CONFIG_MAPPING: dict[str, Any] = {
    "schema_version": 1,
    "label": "synthetic",
    "seed": 20260807,
    "spectrum": {
        "frequency_start_hz": 1419400000.0,
        "frequency_stop_hz": 1421400000.0,
        "n_channels": 601,
        "baseline_volts": 0.05,
        "noise_sigma_volts": 0.0015,
        "line_center_hz": 1420405751.768,
        "line_width_hz": 250000.0,
        "line_peak_volts": 0.02,
    },
    "interference": {
        "spikes": [
            {"center_hz": 1419700000.0, "width_channels": 3, "amplitude_volts": 0.25},
            {"center_hz": 1420900000.0, "width_channels": 1, "amplitude_volts": 0.4},
            {"center_hz": 1421150000.0, "width_channels": 5, "amplitude_volts": 0.18},
        ]
    },
    "cleaning": {"threshold_sigma": 6.0, "window_channels": 15},
    "velocity": {
        "rest_frequency_value": 1420405751.768,
        "rest_frequency_unit": "Hz",
        "doppler_convention": "relativistic",
    },
}

_TOP_LEVEL_KEYS = frozenset(
    {"schema_version", "label", "seed", "spectrum", "interference", "cleaning", "velocity"}
)
_SPECTRUM_KEYS = frozenset(
    {
        "frequency_start_hz",
        "frequency_stop_hz",
        "n_channels",
        "baseline_volts",
        "noise_sigma_volts",
        "line_center_hz",
        "line_width_hz",
        "line_peak_volts",
    }
)
_INTERFERENCE_KEYS = frozenset({"spikes"})
_SPIKE_KEYS = frozenset({"center_hz", "width_channels", "amplitude_volts"})
_CLEANING_KEYS = frozenset({"threshold_sigma", "window_channels"})
_VELOCITY_KEYS = frozenset({"rest_frequency_value", "rest_frequency_unit", "doppler_convention"})


def _section(mapping: Any, name: str, allowed: frozenset[str]) -> dict[str, Any]:
    if not isinstance(mapping, dict):
        raise ConfigurationError(f"{name} must be a JSON object; got {type(mapping).__name__}.")
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise ConfigurationError(
            f"unknown configuration key(s) in {name}: {', '.join(unknown)}. Unknown keys are "
            "rejected so that an unsupported stage cannot be requested silently."
        )
    missing = sorted(allowed - set(mapping))
    if missing:
        raise ConfigurationError(f"missing configuration key(s) in {name}: {', '.join(missing)}.")
    return mapping


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConfigurationError(f"{name} must be a number; got {type(value).__name__}.")
    number = float(value)
    if not math.isfinite(number):
        raise ConfigurationError(f"{name} must be finite; got {value!r}.")
    return number


def _positive(value: Any, name: str) -> float:
    number = _number(value, name)
    if number <= 0.0:
        raise ConfigurationError(f"{name} must be strictly positive; got {number!r}.")
    return number


def _non_negative(value: Any, name: str) -> float:
    number = _number(value, name)
    if number < 0.0:
        raise ConfigurationError(f"{name} must not be negative; got {number!r}.")
    return number


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{name} must be an integer; got {type(value).__name__}.")
    return int(value)


def _positive_integer(value: Any, name: str) -> int:
    number = _integer(value, name)
    if number <= 0:
        raise ConfigurationError(f"{name} must be strictly positive; got {number}.")
    return number


@dataclass(frozen=True)
class SpectrumConfig:
    """Synthetic spectrum geometry and content, all units explicit in the field names."""

    frequency_start_hz: float
    frequency_stop_hz: float
    n_channels: int
    baseline_volts: float
    noise_sigma_volts: float
    line_center_hz: float
    line_width_hz: float
    line_peak_volts: float

    def to_mapping(self) -> dict[str, Any]:
        return {
            "frequency_start_hz": self.frequency_start_hz,
            "frequency_stop_hz": self.frequency_stop_hz,
            "n_channels": self.n_channels,
            "baseline_volts": self.baseline_volts,
            "noise_sigma_volts": self.noise_sigma_volts,
            "line_center_hz": self.line_center_hz,
            "line_width_hz": self.line_width_hz,
            "line_peak_volts": self.line_peak_volts,
        }


@dataclass(frozen=True)
class InterferenceSpike:
    """One deterministic synthetic narrow-band interference feature."""

    center_hz: float
    width_channels: int
    amplitude_volts: float

    def to_mapping(self) -> dict[str, Any]:
        return {
            "center_hz": self.center_hz,
            "width_channels": self.width_channels,
            "amplitude_volts": self.amplitude_volts,
        }


@dataclass(frozen=True)
class InterferenceConfig:
    """The full set of synthetic interference features to inject."""

    spikes: tuple[InterferenceSpike, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {"spikes": [spike.to_mapping() for spike in self.spikes]}


@dataclass(frozen=True)
class CleaningConfig:
    """Parameters of the deterministic interference-masking strategy."""

    threshold_sigma: float
    window_channels: int

    def to_mapping(self) -> dict[str, Any]:
        return {
            "threshold_sigma": self.threshold_sigma,
            "window_channels": self.window_channels,
        }


@dataclass(frozen=True)
class VelocityConfig:
    """Explicit rest frequency and Doppler convention for the synthetic conversion."""

    rest_frequency_value: float
    rest_frequency_unit: str
    doppler_convention: str

    @property
    def rest_frequency(self) -> u.Quantity:
        """The rest frequency as an explicit astropy quantity."""
        return self.rest_frequency_value * u.Unit(self.rest_frequency_unit)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "rest_frequency_value": self.rest_frequency_value,
            "rest_frequency_unit": self.rest_frequency_unit,
            "doppler_convention": self.doppler_convention,
        }


@dataclass(frozen=True)
class DemoConfig:
    """A fully validated configuration for one deterministic synthetic demo run."""

    schema_version: int
    label: str
    seed: int
    spectrum: SpectrumConfig
    interference: InterferenceConfig
    cleaning: CleaningConfig
    velocity: VelocityConfig

    def with_seed(self, seed: int) -> DemoConfig:
        """Return a copy of this configuration with a validated replacement seed."""
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ConfigurationError(f"seed must be an integer; got {type(seed).__name__}.")
        if seed < 0:
            raise ConfigurationError(f"seed must not be negative; got {seed}.")
        return replace(self, seed=seed)

    def to_mapping(self) -> dict[str, Any]:
        """Return the configuration as a plain, JSON-serialisable mapping."""
        return {
            "schema_version": self.schema_version,
            "label": self.label,
            "seed": self.seed,
            "spectrum": self.spectrum.to_mapping(),
            "interference": self.interference.to_mapping(),
            "cleaning": self.cleaning.to_mapping(),
            "velocity": self.velocity.to_mapping(),
        }


def canonical_json(config: DemoConfig) -> str:
    """Return the configuration as canonical JSON: sorted keys, fixed separators."""
    return json.dumps(config.to_mapping(), sort_keys=True, separators=(",", ":"))


def config_checksum(config: DemoConfig) -> str:
    """Return the SHA-256 of the configuration's canonical JSON form."""
    return hashlib.sha256(canonical_json(config).encode("utf-8")).hexdigest()


def _parse_spectrum(mapping: Any) -> SpectrumConfig:
    section = _section(mapping, "spectrum", _SPECTRUM_KEYS)
    start = _positive(section["frequency_start_hz"], "spectrum.frequency_start_hz")
    stop = _positive(section["frequency_stop_hz"], "spectrum.frequency_stop_hz")
    if stop <= start:
        raise ConfigurationError(
            "spectrum.frequency_stop_hz must be greater than spectrum.frequency_start_hz; got "
            f"{stop!r} and {start!r}."
        )
    n_channels = _integer(section["n_channels"], "spectrum.n_channels")
    if n_channels < MIN_CHANNELS:
        raise ConfigurationError(
            f"spectrum.n_channels must be at least {MIN_CHANNELS}; got {n_channels}."
        )
    line_center = _positive(section["line_center_hz"], "spectrum.line_center_hz")
    if not start <= line_center <= stop:
        raise ConfigurationError(
            "spectrum.line_center_hz must lie within the spectrum band "
            f"[{start!r}, {stop!r}]; got {line_center!r}."
        )
    return SpectrumConfig(
        frequency_start_hz=start,
        frequency_stop_hz=stop,
        n_channels=n_channels,
        baseline_volts=_number(section["baseline_volts"], "spectrum.baseline_volts"),
        noise_sigma_volts=_non_negative(section["noise_sigma_volts"], "spectrum.noise_sigma_volts"),
        line_center_hz=line_center,
        line_width_hz=_positive(section["line_width_hz"], "spectrum.line_width_hz"),
        line_peak_volts=_number(section["line_peak_volts"], "spectrum.line_peak_volts"),
    )


def _parse_interference(mapping: Any, spectrum: SpectrumConfig) -> InterferenceConfig:
    section = _section(mapping, "interference", _INTERFERENCE_KEYS)
    raw_spikes = section["spikes"]
    if not isinstance(raw_spikes, list):
        raise ConfigurationError("interference.spikes must be a JSON array.")
    if not raw_spikes:
        raise ConfigurationError(
            "interference.spikes must contain at least one spike; the demo exists to show "
            "injection and removal."
        )
    spikes = []
    for index, raw in enumerate(raw_spikes):
        name = f"interference.spikes[{index}]"
        spike_section = _section(raw, name, _SPIKE_KEYS)
        center = _positive(spike_section["center_hz"], f"{name}.center_hz")
        if not spectrum.frequency_start_hz <= center <= spectrum.frequency_stop_hz:
            raise ConfigurationError(
                f"{name}.center_hz must lie within the spectrum band "
                f"[{spectrum.frequency_start_hz!r}, {spectrum.frequency_stop_hz!r}]; "
                f"got {center!r}."
            )
        width = _positive_integer(spike_section["width_channels"], f"{name}.width_channels")
        if width % 2 == 0:
            raise ConfigurationError(
                f"{name}.width_channels must be odd so the spike is centred on a channel; "
                f"got {width}."
            )
        spikes.append(
            InterferenceSpike(
                center_hz=center,
                width_channels=width,
                amplitude_volts=_number(
                    spike_section["amplitude_volts"], f"{name}.amplitude_volts"
                ),
            )
        )
    return InterferenceConfig(spikes=tuple(spikes))


def _parse_cleaning(mapping: Any) -> CleaningConfig:
    section = _section(mapping, "cleaning", _CLEANING_KEYS)
    window = _positive_integer(section["window_channels"], "cleaning.window_channels")
    if window % 2 == 0:
        raise ConfigurationError(
            f"cleaning.window_channels must be odd so the window is centred; got {window}."
        )
    return CleaningConfig(
        threshold_sigma=_positive(section["threshold_sigma"], "cleaning.threshold_sigma"),
        window_channels=window,
    )


def _parse_velocity(mapping: Any) -> VelocityConfig:
    section = _section(mapping, "velocity", _VELOCITY_KEYS)
    unit_name = section["rest_frequency_unit"]
    if not isinstance(unit_name, str):
        raise ConfigurationError(
            f"velocity.rest_frequency_unit must be a string naming a frequency unit; "
            f"got {type(unit_name).__name__}."
        )
    try:
        unit = u.Unit(unit_name)
    except ValueError as error:
        raise ConfigurationError(
            f"velocity.rest_frequency_unit is not a recognised unit: {unit_name!r}."
        ) from error
    if not unit.is_equivalent(u.Hz):
        raise ConfigurationError(
            f"velocity.rest_frequency_unit must be a frequency unit; got {unit_name!r}."
        )
    convention = section["doppler_convention"]
    if convention not in SUPPORTED_CONVENTIONS:
        raise ConfigurationError(
            f"velocity.doppler_convention must name a supported Doppler convention "
            f"({', '.join(SUPPORTED_CONVENTIONS)}); got {convention!r}."
        )
    return VelocityConfig(
        rest_frequency_value=_positive(
            section["rest_frequency_value"], "velocity.rest_frequency_value"
        ),
        rest_frequency_unit=unit_name,
        doppler_convention=convention,
    )


def config_from_mapping(mapping: Any) -> DemoConfig:
    """Validate a plain mapping and return a :class:`DemoConfig`."""
    section = _section(mapping, "configuration", _TOP_LEVEL_KEYS)

    schema_version = _integer(section["schema_version"], "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ConfigurationError(
            f"unsupported schema_version {schema_version}; this package understands "
            f"schema_version {SCHEMA_VERSION}."
        )
    label = section["label"]
    if label != SYNTHETIC_LABEL:
        raise ConfigurationError(
            f"label must be {SYNTHETIC_LABEL!r}; this package configures no measured "
            f"observation, and {label!r} was supplied."
        )
    seed = _integer(section["seed"], "seed")
    if seed < 0:
        raise ConfigurationError(f"seed must not be negative; got {seed}.")

    spectrum = _parse_spectrum(section["spectrum"])
    return DemoConfig(
        schema_version=schema_version,
        label=label,
        seed=seed,
        spectrum=spectrum,
        interference=_parse_interference(section["interference"], spectrum),
        cleaning=_parse_cleaning(section["cleaning"]),
        velocity=_parse_velocity(section["velocity"]),
    )


def load_config(path: Path) -> DemoConfig:
    """Load and validate a JSON configuration file."""
    path = Path(path)
    if not path.is_file():
        raise ConfigurationError(f"configuration file does not exist: {path.name}")
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigurationError(f"{path.name} is not valid JSON: {error.msg}") from error
    return config_from_mapping(mapping)


def default_config() -> DemoConfig:
    """Return the validated built-in default configuration."""
    return config_from_mapping(copy.deepcopy(DEFAULT_CONFIG_MAPPING))
