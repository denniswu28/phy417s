"""Frequency-to-velocity conversion under an explicit rest frequency and convention.

The conversion is a synthetic-demonstration convention only. These tests assert
software behaviour; none of them validates a scientific result, a reference
frame, or the historical implementation described in the accepted audit.
"""

from __future__ import annotations

import astropy.units as u
import numpy as np
import pytest

from galaxy_structure.errors import UnitError
from galaxy_structure.spectrum import Spectrum
from galaxy_structure.velocity import (
    NIST_HYDROGEN_HYPERFINE_FREQUENCY_HZ,
    ROUND_TRIP_RTOL,
    frequency_to_velocity,
    velocity_table,
    velocity_to_frequency,
)

REST = NIST_HYDROGEN_HYPERFINE_FREQUENCY_HZ * u.Hz


def test_nist_rest_frequency_matches_the_cited_recommended_value() -> None:
    assert NIST_HYDROGEN_HYPERFINE_FREQUENCY_HZ == 1420405751.768


def test_rest_frequency_maps_to_zero_velocity() -> None:
    velocity = frequency_to_velocity(REST, rest_frequency=REST, convention="relativistic")

    assert velocity.unit.is_equivalent(u.km / u.s)
    assert velocity.to_value(u.km / u.s) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("convention", ["relativistic", "radio", "optical"])
def test_rest_frequency_maps_to_zero_velocity_for_every_convention(convention: str) -> None:
    velocity = frequency_to_velocity(REST, rest_frequency=REST, convention=convention)

    assert velocity.to_value(u.km / u.s) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("convention", ["relativistic", "radio", "optical"])
def test_frequency_velocity_round_trip_within_documented_tolerance(convention: str) -> None:
    frequency = np.linspace(1.4194e9, 1.4214e9, 601) * u.Hz

    velocity = frequency_to_velocity(frequency, rest_frequency=REST, convention=convention)
    restored = velocity_to_frequency(velocity, rest_frequency=REST, convention=convention)

    np.testing.assert_allclose(
        restored.to_value(u.Hz), frequency.to_value(u.Hz), rtol=ROUND_TRIP_RTOL, atol=0.0
    )


def test_velocity_increases_as_frequency_decreases() -> None:
    frequency = np.array([1.4194e9, 1.4204e9, 1.4214e9]) * u.Hz

    velocity = frequency_to_velocity(frequency, rest_frequency=REST, convention="relativistic")

    assert np.all(np.diff(velocity.to_value(u.km / u.s)) < 0.0)


def test_rest_frequency_scale_is_irrelevant_when_units_are_declared() -> None:
    frequency = np.linspace(1.4194e9, 1.4214e9, 5) * u.Hz

    in_hz = frequency_to_velocity(frequency, rest_frequency=REST, convention="relativistic")
    in_mhz = frequency_to_velocity(
        frequency,
        rest_frequency=(NIST_HYDROGEN_HYPERFINE_FREQUENCY_HZ / 1e6) * u.MHz,
        convention="relativistic",
    )

    np.testing.assert_allclose(in_mhz.to_value(u.km / u.s), in_hz.to_value(u.km / u.s), rtol=1e-15)


def test_bare_float_rest_frequency_is_rejected() -> None:
    with pytest.raises(UnitError, match="explicit unit"):
        frequency_to_velocity(
            REST, rest_frequency=NIST_HYDROGEN_HYPERFINE_FREQUENCY_HZ, convention="relativistic"
        )


def test_bare_float_frequency_is_rejected() -> None:
    with pytest.raises(UnitError, match="explicit unit"):
        frequency_to_velocity(1.4204e9, rest_frequency=REST, convention="relativistic")


def test_incompatible_rest_frequency_unit_is_rejected() -> None:
    with pytest.raises(UnitError, match="frequency"):
        frequency_to_velocity(REST, rest_frequency=2.1 * u.m, convention="relativistic")


def test_incompatible_input_unit_is_rejected() -> None:
    with pytest.raises(UnitError, match="frequency"):
        frequency_to_velocity(21.0 * u.cm, rest_frequency=REST, convention="relativistic")


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_non_positive_rest_frequency_is_rejected(bad: float) -> None:
    with pytest.raises(UnitError, match="positive"):
        frequency_to_velocity(REST, rest_frequency=bad * u.Hz, convention="relativistic")


def test_non_scalar_rest_frequency_is_rejected() -> None:
    with pytest.raises(UnitError, match="scalar"):
        frequency_to_velocity(
            REST, rest_frequency=np.array([1.0, 2.0]) * u.Hz, convention="relativistic"
        )


def test_non_finite_frequency_is_rejected() -> None:
    frequency = np.array([1.4194e9, np.nan, 1.4214e9]) * u.Hz

    with pytest.raises(UnitError, match="non-finite"):
        frequency_to_velocity(frequency, rest_frequency=REST, convention="relativistic")


def test_unknown_convention_is_rejected() -> None:
    with pytest.raises(UnitError, match="convention"):
        frequency_to_velocity(REST, rest_frequency=REST, convention="newtonian")


def test_convention_must_be_supplied_explicitly() -> None:
    with pytest.raises(TypeError):
        frequency_to_velocity(REST, rest_frequency=REST)  # type: ignore[call-arg]


def test_velocity_table_reports_units_convention_and_frame_boundary() -> None:
    spectrum = Spectrum(
        frequency_hz=np.linspace(1.4194e9, 1.4214e9, 7), amplitude_volts=np.zeros(7)
    )

    table = velocity_table(spectrum, rest_frequency=REST, convention="relativistic")

    assert table.frequency_unit == "Hz"
    assert table.velocity_unit == "km / s"
    assert table.amplitude_unit == "Volts"
    assert table.convention == "relativistic"
    assert table.rest_frequency_hz == NIST_HYDROGEN_HYPERFINE_FREQUENCY_HZ
    assert table.reference_frame == "none-applied"
    assert table.label == "synthetic"
    assert table.velocity_km_s.shape == (7,)
    np.testing.assert_array_equal(table.frequency_hz, spectrum.frequency_hz)


def test_velocity_table_writes_a_deterministic_labelled_csv(tmp_path) -> None:
    spectrum = Spectrum(
        frequency_hz=np.linspace(1.4194e9, 1.4214e9, 7), amplitude_volts=np.linspace(0, 1, 7)
    )
    table = velocity_table(spectrum, rest_frequency=REST, convention="relativistic")
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"

    table.write(first)
    table.write(second)

    text = first.read_text(encoding="utf-8")
    assert first.read_bytes() == second.read_bytes()
    assert "synthetic" in text.lower()
    assert "frequency_hz,velocity_km_s,amplitude_volts" in text
    assert len(text.strip().splitlines()) == 7 + 1 + text.count("#")
