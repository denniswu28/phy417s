"""Deterministic PNG figure rendering and figure provenance.

Committed figures must be regenerable byte for byte, so no run-varying field --
creation time, host, user, absolute path, or random identifier -- may reach the
PNG bytes.
"""

from __future__ import annotations

import struct
from pathlib import Path

import astropy.units as u
import pytest

from galaxy_structure.config import load_config
from galaxy_structure.interference import clean_interference, inject_interference
from galaxy_structure.plotting import (
    BEFORE_AFTER_CLAIM_ID,
    SYNTHETIC_FIGURE_LABEL,
    VELOCITY_MAPPING_CLAIM_ID,
    plot_before_after,
    plot_frequency_velocity,
)
from galaxy_structure.synthetic import generate_spectrum
from galaxy_structure.velocity import velocity_table

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG_PATH = REPO_ROOT / "config" / "demo.json"


@pytest.fixture
def pipeline():
    config = load_config(DEMO_CONFIG_PATH)
    original = generate_spectrum(config)
    injected = inject_interference(original, config.interference)
    cleaned = clean_interference(injected.spectrum, config.cleaning)
    table = velocity_table(
        cleaned.spectrum,
        rest_frequency=config.velocity.rest_frequency,
        convention=config.velocity.doppler_convention,
    )
    return config, original, injected, cleaned, table


def png_text_chunks(path: Path) -> dict[str, str]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    chunks: dict[str, str] = {}
    offset = 8
    while offset < len(data):
        (length,) = struct.unpack(">I", data[offset : offset + 4])
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        if kind in (b"tEXt", b"iTXt", b"zTXt"):
            key, _, value = payload.partition(b"\x00")
            chunks[key.decode("latin-1")] = value.decode("latin-1", errors="replace")
        if kind == b"tIME":
            chunks["tIME"] = payload.hex()
        offset += 12 + length
    return chunks


def test_before_after_figure_is_byte_identical_across_renders(pipeline, tmp_path) -> None:
    _, original, injected, cleaned, _ = pipeline
    first = tmp_path / "a.png"
    second = tmp_path / "b.png"

    plot_before_after(original=original, injected=injected.spectrum, cleaned=cleaned, path=first)
    plot_before_after(original=original, injected=injected.spectrum, cleaned=cleaned, path=second)

    assert first.read_bytes() == second.read_bytes()


def test_velocity_mapping_figure_is_byte_identical_across_renders(pipeline, tmp_path) -> None:
    *_, table = pipeline
    first = tmp_path / "a.png"
    second = tmp_path / "b.png"

    plot_frequency_velocity(table=table, path=first)
    plot_frequency_velocity(table=table, path=second)

    assert first.read_bytes() == second.read_bytes()


def test_before_after_figure_carries_no_run_varying_metadata(pipeline, tmp_path) -> None:
    _, original, injected, cleaned, _ = pipeline
    path = tmp_path / "figure.png"

    plot_before_after(original=original, injected=injected.spectrum, cleaned=cleaned, path=path)

    chunks = png_text_chunks(path)
    assert "Software" not in chunks
    assert "tIME" not in chunks
    assert "Creation Time" not in chunks
    for value in chunks.values():
        assert str(tmp_path) not in value


def test_figure_record_declares_units_label_frame_and_claim(pipeline, tmp_path) -> None:
    _, original, injected, cleaned, _ = pipeline

    record = plot_before_after(
        original=original, injected=injected.spectrum, cleaned=cleaned, path=tmp_path / "f.png"
    )

    assert record.filename == "f.png"
    assert record.claim_id == BEFORE_AFTER_CLAIM_ID
    assert SYNTHETIC_FIGURE_LABEL in record.caption
    assert record.x_axis_unit == "Hz"
    assert record.y_axis_unit == "Volts"
    assert record.label == "synthetic"
    assert record.reference_frame == "none-applied"


def test_velocity_figure_record_declares_velocity_units_and_frame(pipeline, tmp_path) -> None:
    *_, table = pipeline

    record = plot_frequency_velocity(table=table, path=tmp_path / "v.png")

    assert record.claim_id == VELOCITY_MAPPING_CLAIM_ID
    assert SYNTHETIC_FIGURE_LABEL in record.caption
    assert record.x_axis_unit == "Hz"
    assert record.y_axis_unit == "km / s"
    assert record.reference_frame == "none-applied"


def test_figure_record_mapping_is_json_safe(pipeline, tmp_path) -> None:
    *_, table = pipeline

    mapping = plot_frequency_velocity(table=table, path=tmp_path / "v.png").to_mapping()

    assert set(mapping) == {
        "filename",
        "claim_id",
        "caption",
        "x_axis_unit",
        "y_axis_unit",
        "label",
        "reference_frame",
    }
    assert all(isinstance(value, str) for value in mapping.values())


def test_plotting_never_recomputes_physics(pipeline, tmp_path) -> None:
    # The velocity figure must plot exactly the velocities it was handed.
    *_, table = pipeline
    expected = table.velocity_km_s.copy()

    plot_frequency_velocity(table=table, path=tmp_path / "v.png")

    assert table.velocity_km_s.tolist() == expected.tolist()
    assert table.velocity_unit == str(u.km / u.s)
