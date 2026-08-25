"""Deterministic synthetic interference injection, masking, and cleaning.

These tests demonstrate a software strategy on synthetic interference. They are
not evidence of scientifically validated interference removal or signal
preservation on any real observation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from galaxy_structure.config import config_from_mapping, load_config
from galaxy_structure.errors import InterferenceError
from galaxy_structure.interference import clean_interference, inject_interference
from galaxy_structure.spectrum import Spectrum
from galaxy_structure.synthetic import generate_spectrum

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG_PATH = REPO_ROOT / "config" / "demo.json"


@pytest.fixture
def config():
    return load_config(DEMO_CONFIG_PATH)


@pytest.fixture
def clean_spectrum(config):
    return generate_spectrum(config)


def test_injection_is_deterministic(config, clean_spectrum) -> None:
    first = inject_interference(clean_spectrum, config.interference)
    second = inject_interference(clean_spectrum, config.interference)

    np.testing.assert_array_equal(first.spectrum.amplitude_volts, second.spectrum.amplitude_volts)
    np.testing.assert_array_equal(first.injected_indices, second.injected_indices)


def test_injection_leaves_the_frequency_axis_untouched(config, clean_spectrum) -> None:
    injected = inject_interference(clean_spectrum, config.interference)

    np.testing.assert_array_equal(injected.spectrum.frequency_hz, clean_spectrum.frequency_hz)


def test_injection_changes_only_the_recorded_channels(config, clean_spectrum) -> None:
    injected = inject_interference(clean_spectrum, config.interference)

    changed = np.flatnonzero(injected.spectrum.amplitude_volts != clean_spectrum.amplitude_volts)

    np.testing.assert_array_equal(changed, injected.injected_indices)


def test_injection_covers_every_configured_spike_width(config, clean_spectrum) -> None:
    injected = inject_interference(clean_spectrum, config.interference)

    expected_width = sum(spike.width_channels for spike in config.interference.spikes)

    assert injected.injected_indices.size == expected_width


def test_injection_rejects_a_foreign_frequency_grid(config) -> None:
    other = Spectrum(frequency_hz=np.linspace(1.0e9, 1.1e9, 51), amplitude_volts=np.zeros(51))

    with pytest.raises(InterferenceError, match="within the spectrum band"):
        inject_interference(other, config.interference)


def test_cleaning_is_deterministic(config, clean_spectrum) -> None:
    injected = inject_interference(clean_spectrum, config.interference).spectrum

    first = clean_interference(injected, config.cleaning)
    second = clean_interference(injected, config.cleaning)

    np.testing.assert_array_equal(first.spectrum.amplitude_volts, second.spectrum.amplitude_volts)
    np.testing.assert_array_equal(first.mask, second.mask)


def test_cleaning_preserves_every_unmasked_sample_exactly(config, clean_spectrum) -> None:
    injected = inject_interference(clean_spectrum, config.interference).spectrum

    result = clean_interference(injected, config.cleaning)

    unmasked = ~result.mask
    np.testing.assert_array_equal(
        result.spectrum.amplitude_volts[unmasked], injected.amplitude_volts[unmasked]
    )


def test_every_altered_sample_is_recorded_in_the_mask(config, clean_spectrum) -> None:
    injected = inject_interference(clean_spectrum, config.interference).spectrum

    result = clean_interference(injected, config.cleaning)

    altered = np.flatnonzero(result.spectrum.amplitude_volts != injected.amplitude_volts)
    np.testing.assert_array_equal(altered, result.altered_indices)
    assert np.all(result.mask[altered])


def test_cleaning_masks_every_injected_spike_channel(config, clean_spectrum) -> None:
    injected = inject_interference(clean_spectrum, config.interference)

    result = clean_interference(injected.spectrum, config.cleaning)

    assert np.all(result.mask[injected.injected_indices])


def test_cleaning_preserves_the_synthetic_line(config, clean_spectrum) -> None:
    injected = inject_interference(clean_spectrum, config.interference)

    result = clean_interference(injected.spectrum, config.cleaning)

    line_channel = int(
        np.argmin(np.abs(clean_spectrum.frequency_hz - config.spectrum.line_center_hz))
    )
    assert not result.mask[line_channel]
    assert (
        result.spectrum.amplitude_volts[line_channel]
        == clean_spectrum.amplitude_volts[line_channel]
    )


def test_cleaning_a_spectrum_without_interference_masks_nothing(clean_spectrum, config) -> None:
    result = clean_interference(clean_spectrum, config.cleaning)

    assert result.mask.sum() == 0
    np.testing.assert_array_equal(result.spectrum.amplitude_volts, clean_spectrum.amplitude_volts)


def test_a_degenerate_spectrum_with_no_scatter_is_left_untouched(config) -> None:
    mapping = json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))
    mapping["spectrum"]["noise_sigma_volts"] = 0.0
    mapping["spectrum"]["line_peak_volts"] = 0.0
    flat = generate_spectrum(config_from_mapping(mapping))

    result = clean_interference(flat, config.cleaning)

    assert result.mask.sum() == 0
    np.testing.assert_array_equal(result.spectrum.amplitude_volts, flat.amplitude_volts)


def test_a_feature_wider_than_half_the_window_is_not_flagged(config, clean_spectrum) -> None:
    # Documented limitation: the running median follows any feature that occupies
    # at least half of its window, so such a feature cannot be flagged. The demo
    # configuration keeps every spike well below that limit.
    mapping = json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))
    mapping["interference"]["spikes"] = [
        {
            "center_hz": 1420000000.0,
            "width_channels": config.cleaning.window_channels,
            "amplitude_volts": 1.0,
        }
    ]
    wide = config_from_mapping(mapping)

    injected = inject_interference(clean_spectrum, wide.interference)
    result = clean_interference(injected.spectrum, config.cleaning)

    assert not np.all(result.mask[injected.injected_indices])


def test_cleaning_rejects_a_window_wider_than_the_spectrum(config) -> None:
    short = Spectrum(frequency_hz=np.linspace(1.4194e9, 1.4214e9, 3), amplitude_volts=np.zeros(3))

    with pytest.raises(InterferenceError, match="wider than"):
        clean_interference(short, config.cleaning)


def test_mask_record_is_written_deterministically_and_labelled(
    config, clean_spectrum, tmp_path
) -> None:
    injected = inject_interference(clean_spectrum, config.interference).spectrum
    result = clean_interference(injected, config.cleaning)
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"

    result.write_mask(first)
    result.write_mask(second)

    text = first.read_text(encoding="utf-8")
    assert first.read_bytes() == second.read_bytes()
    assert "synthetic" in text.lower()
    assert "channel_index,frequency_hz,original_volts,cleaned_volts" in text
    data_rows = [
        line
        for line in text.splitlines()
        if line and not line.startswith("#") and not line.startswith("channel_index")
    ]
    assert len(data_rows) == int(result.mask.sum())
