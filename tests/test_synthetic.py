"""Deterministic synthetic-spectrum generation.

Everything generated here is synthetic. No test in this file reads a measured
file, and no assertion here is evidence about a real observation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from galaxy_structure.config import config_from_mapping, load_config
from galaxy_structure.spectrum import SYNTHETIC_LABEL, Spectrum
from galaxy_structure.synthetic import RANDOM_GENERATOR_REFERENCE_URL, generate_spectrum

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG_PATH = REPO_ROOT / "config" / "demo.json"


@pytest.fixture
def config():
    return load_config(DEMO_CONFIG_PATH)


def test_generated_spectrum_matches_the_configured_grid(config) -> None:
    spectrum = generate_spectrum(config)

    assert isinstance(spectrum, Spectrum)
    assert spectrum.label == SYNTHETIC_LABEL
    assert spectrum.n_channels == config.spectrum.n_channels
    assert spectrum.frequency_hz[0] == pytest.approx(config.spectrum.frequency_start_hz)
    assert spectrum.frequency_hz[-1] == pytest.approx(config.spectrum.frequency_stop_hz)
    assert np.all(np.diff(spectrum.frequency_hz) > 0.0)


def test_same_seed_reproduces_identical_amplitudes(config) -> None:
    first = generate_spectrum(config)
    second = generate_spectrum(config)

    np.testing.assert_array_equal(first.amplitude_volts, second.amplitude_volts)
    np.testing.assert_array_equal(first.frequency_hz, second.frequency_hz)


def test_different_seed_changes_amplitudes_but_not_the_grid(config) -> None:
    baseline = generate_spectrum(config)
    reseeded = generate_spectrum(config.with_seed(config.seed + 1))

    np.testing.assert_array_equal(reseeded.frequency_hz, baseline.frequency_hz)
    assert not np.array_equal(reseeded.amplitude_volts, baseline.amplitude_volts)


def test_zero_noise_yields_exactly_baseline_plus_line(config) -> None:
    mapping = json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))
    mapping["spectrum"]["noise_sigma_volts"] = 0.0
    noiseless = generate_spectrum(config_from_mapping(mapping))

    # The configured line center does not fall exactly on a channel, so the
    # sampled maximum sits marginally below the analytic peak.
    expected_peak = config.spectrum.baseline_volts + config.spectrum.line_peak_volts
    assert noiseless.amplitude_volts.max() == pytest.approx(expected_peak, rel=1e-4)
    assert noiseless.amplitude_volts.max() <= expected_peak
    # The Gaussian feature never reaches zero, so the band edge sits just above
    # the baseline rather than exactly on it.
    tail = noiseless.amplitude_volts.min() - config.spectrum.baseline_volts
    assert 0.0 <= tail < 0.01 * config.spectrum.line_peak_volts


def test_line_peak_sits_at_the_configured_line_center(config) -> None:
    mapping = json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))
    mapping["spectrum"]["noise_sigma_volts"] = 0.0
    noiseless = generate_spectrum(config_from_mapping(mapping))

    peak_frequency = noiseless.frequency_hz[int(np.argmax(noiseless.amplitude_volts))]

    assert abs(peak_frequency - config.spectrum.line_center_hz) <= noiseless.channel_width_hz


def test_generator_boundary_is_documented() -> None:
    assert RANDOM_GENERATOR_REFERENCE_URL.startswith(
        "https://numpy.org/doc/stable/reference/random"
    )


def test_noise_is_drawn_from_the_seeded_default_generator(config) -> None:
    mapping = json.loads(DEMO_CONFIG_PATH.read_text(encoding="utf-8"))
    mapping["spectrum"]["baseline_volts"] = 0.0
    mapping["spectrum"]["line_peak_volts"] = 0.0
    only_noise = generate_spectrum(config_from_mapping(mapping))

    expected = np.random.default_rng(config.seed).normal(
        loc=0.0, scale=config.spectrum.noise_sigma_volts, size=config.spectrum.n_channels
    )

    np.testing.assert_array_equal(only_noise.amplitude_volts, expected)
