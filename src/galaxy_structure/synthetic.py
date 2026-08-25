"""Deterministic synthetic-spectrum generation.

Everything produced here is synthetic. The output resembles the *shape* of a
two-column spectrum -- a baseline, a broad emission-like feature, and Gaussian
noise -- so that the downstream software stages have something to operate on. It
is not a simulation of an instrument, a sky model, or an observation, and it
reproduces no measured file.

Randomness comes from an explicitly seeded :func:`numpy.random.default_rng`
generator. NumPy documents the generator and its stability boundary at
https://numpy.org/doc/stable/reference/random/ -- reproducibility is guaranteed
for a fixed seed within a fixed NumPy version, which is why
``constraints-ci.txt`` pins NumPy exactly.
"""

from __future__ import annotations

import numpy as np

from .config import DemoConfig
from .spectrum import Spectrum

#: Primary documentation for the random-number generator boundary.
RANDOM_GENERATOR_REFERENCE_URL = "https://numpy.org/doc/stable/reference/random/"


def frequency_grid(config: DemoConfig) -> np.ndarray:
    """Return the configured strictly increasing, uniform frequency grid in hertz."""
    return np.linspace(
        config.spectrum.frequency_start_hz,
        config.spectrum.frequency_stop_hz,
        config.spectrum.n_channels,
        dtype=np.float64,
    )


def generate_spectrum(config: DemoConfig) -> Spectrum:
    """Generate the deterministic synthetic spectrum described by ``config``.

    The amplitude is ``baseline + Gaussian feature + Gaussian noise``. The noise
    is drawn from ``numpy.random.default_rng(config.seed)``, so two runs with the
    same configuration and seed produce identical arrays.
    """
    frequency = frequency_grid(config)
    spectrum_config = config.spectrum

    offset = (frequency - spectrum_config.line_center_hz) / spectrum_config.line_width_hz
    feature = spectrum_config.line_peak_volts * np.exp(-0.5 * np.square(offset))

    rng = np.random.default_rng(config.seed)
    noise = rng.normal(
        loc=0.0, scale=spectrum_config.noise_sigma_volts, size=spectrum_config.n_channels
    )

    amplitude = spectrum_config.baseline_volts + feature + noise
    return Spectrum(frequency_hz=frequency, amplitude_volts=amplitude)
