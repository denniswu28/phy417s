"""Every real-observation stage must fail closed.

No stage below may return a stubbed value, a zero correction, a partial result,
or ``None``. The accepted audit records that the legacy ``vel_correction`` had an
empty body and returned ``None`` for every input; these tests exist so that
failure mode cannot reappear.
"""

from __future__ import annotations

import inspect

import pytest

from galaxy_structure import unavailable
from galaxy_structure.errors import UnavailableStageError

STAGES = [
    "apply_calibration",
    "barycentric_correction",
    "heliocentric_correction",
    "lsr_correction",
    "earth_motion_correction",
    "galactic_radius",
    "rotation_curve",
]


def test_every_documented_stage_is_exported() -> None:
    assert sorted(unavailable.UNAVAILABLE_STAGES) == sorted(STAGES)


@pytest.mark.parametrize("name", STAGES)
def test_stage_is_present_and_callable(name: str) -> None:
    assert callable(getattr(unavailable, name))


@pytest.mark.parametrize("name", STAGES)
def test_stage_fails_closed_rather_than_returning_a_value(name: str) -> None:
    stage = getattr(unavailable, name)
    signature = inspect.signature(stage)
    arguments = [None] * len(
        [p for p in signature.parameters.values() if p.default is inspect.Parameter.empty]
    )

    with pytest.raises(UnavailableStageError):
        stage(*arguments)


@pytest.mark.parametrize("name", STAGES)
def test_stage_error_names_the_stage_and_the_missing_evidence(name: str) -> None:
    stage = getattr(unavailable, name)

    with pytest.raises(UnavailableStageError) as raised:
        stage(None)

    message = str(raised.value)
    assert name in message
    assert "NEEDS_REVIEW" in message
    assert len(message) > 80


def test_reference_frame_stages_cite_the_astropy_requirement() -> None:
    for name in ("barycentric_correction", "heliocentric_correction"):
        with pytest.raises(UnavailableStageError) as raised:
            getattr(unavailable, name)(None)
        assert "docs.astropy.org" in str(raised.value)


def test_rotation_curve_states_that_no_scientific_result_is_produced() -> None:
    with pytest.raises(UnavailableStageError) as raised:
        unavailable.rotation_curve(None)

    message = str(raised.value).lower()
    assert "rotation curve" in message
    assert "synthetic" in message


def test_unavailable_module_defines_no_silently_succeeding_helper() -> None:
    public = [
        name
        for name, value in vars(unavailable).items()
        if not name.startswith("_") and inspect.isfunction(value)
    ]

    assert sorted(public) == sorted(STAGES)
