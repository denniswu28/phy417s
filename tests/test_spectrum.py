"""Schema, unit and grid validation for the two-column synthetic spectrum type."""

from __future__ import annotations

import numpy as np
import pytest

from galaxy_structure.errors import SpectrumSchemaError
from galaxy_structure.spectrum import Spectrum, read_spectrum, write_spectrum


def make_grid(n: int = 8) -> np.ndarray:
    return np.linspace(1.4194e9, 1.4214e9, n)


def test_spectrum_exposes_channel_count_and_width() -> None:
    frequency = make_grid(5)
    spectrum = Spectrum(frequency_hz=frequency, amplitude_volts=np.zeros(5))

    assert spectrum.n_channels == 5
    assert spectrum.channel_width_hz == pytest.approx(5.0e5)


def test_spectrum_rejects_empty_input() -> None:
    with pytest.raises(SpectrumSchemaError, match="at least"):
        Spectrum(frequency_hz=np.array([]), amplitude_volts=np.array([]))


def test_spectrum_rejects_mismatched_column_lengths() -> None:
    with pytest.raises(SpectrumSchemaError, match="same length"):
        Spectrum(frequency_hz=make_grid(5), amplitude_volts=np.zeros(4))


def test_spectrum_rejects_two_dimensional_input() -> None:
    with pytest.raises(SpectrumSchemaError, match="one-dimensional"):
        Spectrum(frequency_hz=make_grid(6).reshape(3, 2), amplitude_volts=np.zeros((3, 2)))


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_spectrum_rejects_non_finite_frequency(bad: float) -> None:
    frequency = make_grid(5)
    frequency[2] = bad
    with pytest.raises(SpectrumSchemaError, match="non-finite"):
        Spectrum(frequency_hz=frequency, amplitude_volts=np.zeros(5))


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_spectrum_rejects_non_finite_amplitude(bad: float) -> None:
    amplitude = np.zeros(5)
    amplitude[1] = bad
    with pytest.raises(SpectrumSchemaError, match="non-finite"):
        Spectrum(frequency_hz=make_grid(5), amplitude_volts=amplitude)


def test_spectrum_rejects_reversed_frequency_axis() -> None:
    with pytest.raises(SpectrumSchemaError, match="strictly increasing"):
        Spectrum(frequency_hz=make_grid(5)[::-1], amplitude_volts=np.zeros(5))


def test_spectrum_rejects_duplicate_frequencies() -> None:
    frequency = make_grid(5)
    frequency[3] = frequency[2]
    with pytest.raises(SpectrumSchemaError, match="strictly increasing"):
        Spectrum(frequency_hz=frequency, amplitude_volts=np.zeros(5))


def test_spectrum_rejects_non_uniform_grid() -> None:
    frequency = make_grid(5)
    frequency[3] += 1.0e4
    with pytest.raises(SpectrumSchemaError, match="uniform"):
        Spectrum(frequency_hz=frequency, amplitude_volts=np.zeros(5))


def test_spectrum_rejects_non_positive_frequency() -> None:
    frequency = np.array([-2.0, -1.0, 0.0, 1.0])
    with pytest.raises(SpectrumSchemaError, match="positive"):
        Spectrum(frequency_hz=frequency, amplitude_volts=np.zeros(4))


def test_spectrum_rejects_measured_label() -> None:
    with pytest.raises(SpectrumSchemaError, match="synthetic"):
        Spectrum(frequency_hz=make_grid(5), amplitude_volts=np.zeros(5), label="measured")


def test_spectrum_arrays_are_read_only_copies() -> None:
    frequency = make_grid(5)
    spectrum = Spectrum(frequency_hz=frequency, amplitude_volts=np.zeros(5))

    frequency[0] = 1.0e9

    assert spectrum.frequency_hz[0] != 1.0e9
    with pytest.raises(ValueError):
        spectrum.frequency_hz[0] = 1.0e9


def test_write_then_read_spectrum_round_trips_exactly(tmp_path) -> None:
    spectrum = Spectrum(
        frequency_hz=make_grid(11),
        amplitude_volts=np.linspace(0.0, 1.0, 11),
    )
    path = tmp_path / "synthetic_spectrum.dat"

    write_spectrum(spectrum, path)
    restored = read_spectrum(path)

    np.testing.assert_array_equal(restored.frequency_hz, spectrum.frequency_hz)
    np.testing.assert_array_equal(restored.amplitude_volts, spectrum.amplitude_volts)
    assert restored.label == "synthetic"


def test_written_spectrum_declares_units_and_synthetic_label(tmp_path) -> None:
    path = tmp_path / "synthetic_spectrum.dat"
    write_spectrum(Spectrum(frequency_hz=make_grid(4), amplitude_volts=np.zeros(4)), path)

    lines = path.read_text(encoding="utf-8").splitlines()
    header = [line for line in lines if line.startswith("#")]

    assert any("Frequency, Hz" in line and "Amplitude, Volts" in line for line in header)
    assert any("synthetic" in line.lower() for line in header)


def test_write_spectrum_is_byte_identical_for_equal_input(tmp_path) -> None:
    spectrum = Spectrum(frequency_hz=make_grid(9), amplitude_volts=np.linspace(-1.0, 1.0, 9))
    first = tmp_path / "a.dat"
    second = tmp_path / "b.dat"

    write_spectrum(spectrum, first)
    write_spectrum(spectrum, second)

    assert first.read_bytes() == second.read_bytes()


def test_read_spectrum_rejects_missing_unit_header(tmp_path) -> None:
    path = tmp_path / "no_header.dat"
    path.write_text("1.0\t2.0\n2.0\t3.0\n3.0\t4.0\n", encoding="utf-8")

    with pytest.raises(SpectrumSchemaError, match="unit header"):
        read_spectrum(path)


def test_read_spectrum_rejects_wrong_column_count(tmp_path) -> None:
    path = tmp_path / "three_columns.dat"
    path.write_text(
        "# synthetic\n# Frequency, Hz\tAmplitude, Volts\n1.0\t2.0\t3.0\n2.0\t3.0\t4.0\n",
        encoding="utf-8",
    )

    with pytest.raises(SpectrumSchemaError, match="two columns"):
        read_spectrum(path)


def test_read_spectrum_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(SpectrumSchemaError, match="does not exist"):
        read_spectrum(tmp_path / "absent.dat")
