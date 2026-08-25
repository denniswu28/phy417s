"""Configuration parsing and validation.

Configuration is the only place a run is parameterised. It fails closed on a
missing key, an unknown key, or an out-of-range value; nothing is defaulted
silently.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from galaxy_structure.config import (
    DemoConfig,
    config_checksum,
    config_from_mapping,
    load_config,
)
from galaxy_structure.errors import ConfigurationError

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG_PATH = REPO_ROOT / "config" / "demo.json"


def demo_mapping() -> dict:
    return json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))


def test_shipped_demo_config_loads() -> None:
    config = load_config(DEMO_CONFIG_PATH)

    assert isinstance(config, DemoConfig)
    assert config.label == "synthetic"
    assert config.spectrum.n_channels == 601
    assert config.spectrum.frequency_start_hz == 1.4194e9
    assert config.spectrum.frequency_stop_hz == 1.4214e9
    assert config.velocity.doppler_convention == "relativistic"
    assert config.velocity.rest_frequency_value == 1420405751.768
    assert config.velocity.rest_frequency_unit == "Hz"
    assert len(config.interference.spikes) >= 1


def test_load_config_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="does not exist"):
        load_config(tmp_path / "absent.json")


def test_load_config_rejects_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="not valid JSON"):
        load_config(path)


def test_unknown_top_level_key_is_rejected() -> None:
    mapping = demo_mapping()
    mapping["extra_stage"] = {"enabled": True}

    with pytest.raises(ConfigurationError, match="unknown"):
        config_from_mapping(mapping)


def test_unknown_nested_key_is_rejected() -> None:
    mapping = demo_mapping()
    mapping["velocity"]["lsr_correction_km_s"] = 12.0

    with pytest.raises(ConfigurationError, match="unknown"):
        config_from_mapping(mapping)


def test_missing_required_key_is_rejected() -> None:
    mapping = demo_mapping()
    del mapping["spectrum"]["n_channels"]

    with pytest.raises(ConfigurationError, match="missing"):
        config_from_mapping(mapping)


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        ("spectrum", "n_channels", 1, "at least"),
        ("spectrum", "n_channels", 2.5, "integer"),
        ("spectrum", "noise_sigma_volts", -1.0, "negative"),
        ("spectrum", "line_width_hz", 0.0, "positive"),
        ("cleaning", "threshold_sigma", 0.0, "positive"),
        ("cleaning", "window_channels", 8, "odd"),
        ("cleaning", "window_channels", -3, "positive"),
        ("velocity", "rest_frequency_value", 0.0, "positive"),
        ("velocity", "doppler_convention", "newtonian", "convention"),
        ("velocity", "rest_frequency_unit", "metre", "frequency"),
    ],
)
def test_out_of_range_values_are_rejected(
    section: str, key: str, value: object, match: str
) -> None:
    mapping = demo_mapping()
    mapping[section][key] = value

    with pytest.raises(ConfigurationError, match=match):
        config_from_mapping(mapping)


def test_non_increasing_frequency_span_is_rejected() -> None:
    mapping = demo_mapping()
    mapping["spectrum"]["frequency_stop_hz"] = mapping["spectrum"]["frequency_start_hz"]

    with pytest.raises(ConfigurationError, match="greater than"):
        config_from_mapping(mapping)


def test_non_finite_value_is_rejected() -> None:
    mapping = demo_mapping()
    mapping["spectrum"]["baseline_volts"] = float("nan")

    with pytest.raises(ConfigurationError, match="finite"):
        config_from_mapping(mapping)


def test_measured_label_is_rejected() -> None:
    mapping = demo_mapping()
    mapping["label"] = "measured"

    with pytest.raises(ConfigurationError, match="synthetic"):
        config_from_mapping(mapping)


def test_unsupported_schema_version_is_rejected() -> None:
    mapping = demo_mapping()
    mapping["schema_version"] = 99

    with pytest.raises(ConfigurationError, match="schema_version"):
        config_from_mapping(mapping)


def test_interference_spike_outside_band_is_rejected() -> None:
    mapping = demo_mapping()
    mapping["interference"]["spikes"][0]["center_hz"] = 1.0e9

    with pytest.raises(ConfigurationError, match="within the spectrum band"):
        config_from_mapping(mapping)


def test_empty_interference_spike_list_is_rejected() -> None:
    mapping = demo_mapping()
    mapping["interference"]["spikes"] = []

    with pytest.raises(ConfigurationError, match="at least one"):
        config_from_mapping(mapping)


def test_seed_must_be_a_non_negative_integer() -> None:
    mapping = demo_mapping()
    mapping["seed"] = -1

    with pytest.raises(ConfigurationError, match="negative"):
        config_from_mapping(mapping)


def test_config_checksum_is_stable_and_order_independent() -> None:
    mapping = demo_mapping()
    reordered = dict(reversed(list(mapping.items())))

    first = config_checksum(config_from_mapping(mapping))
    second = config_checksum(config_from_mapping(reordered))

    assert first == second
    assert len(first) == 64


def test_config_checksum_changes_when_a_value_changes() -> None:
    mapping = demo_mapping()
    changed = copy.deepcopy(mapping)
    changed["spectrum"]["baseline_volts"] += 0.01

    assert config_checksum(config_from_mapping(mapping)) != config_checksum(
        config_from_mapping(changed)
    )


def test_with_seed_returns_a_new_config() -> None:
    config = load_config(DEMO_CONFIG_PATH)

    reseeded = config.with_seed(1234)

    assert reseeded.seed == 1234
    assert config.seed != 1234
    assert config_checksum(reseeded) != config_checksum(config)
