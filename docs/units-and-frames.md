# Units and reference frames

Explicit units and reference frames are a hard requirement here, not a
documentation preference. A unit or frame mismatch is an **error**, never a
silent coercion.

Claim IDs refer to [`claim-evidence.md`](claim-evidence.md).

## Units

| Quantity | Unit | Where it is declared |
| --- | --- | --- |
| Frequency | hertz (`Hz`) | Field names (`frequency_hz`, `line_center_hz`), the `.dat` unit header, the CSV column names, and every figure axis label |
| Amplitude | volts (`Volts`) | Field names (`amplitude_volts`), the `.dat` unit header, the CSV column names, and every figure axis label |
| Radial velocity | kilometres per second (`km / s`) | `VelocityTable.velocity_unit`, the CSV column names, and the figure axis label |
| Rest frequency | any frequency-compatible Astropy unit | `config/demo.json` states the value and the unit separately; the API takes a `Quantity` |

Rules:

1. **The rest frequency is defined once, with its unit.** It is supplied as an
   Astropy `Quantity`, so its scale travels with it. A bare number is rejected
   with a `UnitError`.

   This rule exists for a specific reason. The accepted private audit records
   that the historical source carried the rest frequency as `1420.405751768` in
   one file and `1.420405751768e9` in another — a factor of 10^6 apart — with
   two different Doppler formulas (`GS-UNITS-001`). Declaring the unit makes
   that class of error unrepresentable rather than merely discouraged. A test
   asserts that declaring the value in MHz and in Hz gives identical results.

2. **Incompatible units raise.** A length where a frequency is required, or a
   frequency where a speed is required, is a `UnitError`. Nothing is coerced.

3. **Grids are validated, not repaired.** A descending, duplicated, or
   non-uniform frequency axis is rejected. It is never silently sorted,
   de-duplicated, or resampled.

4. **Angles.** This package accepts no observation longitude or other angle. If
   one is ever added it must declare degrees or radians together with its
   coordinate frame and epoch. The "longitude" labels in the historical
   filenames were a **naming convention only**: no pointing record, frame,
   or epoch accompanies them, and whether they are galactic longitude is
   `TODO(Dennis)`.

## Reference frames

The velocity coordinate this package produces carries **no observational
reference frame** (`GS-FRAME-001`). Every velocity artifact and the run manifest
record this explicitly as:

```text
reference_frame: none-applied
```

It is **not** topocentric, **not** geocentric, **not** barycentric, **not**
heliocentric, and **not** LSR. It is the direct mapping of a synthetic frequency
axis through a declared Doppler convention and a declared rest frequency, and
nothing more.

### Why no frame is applied

A frame correction is not a formula that can be supplied from a document. It
needs observation-specific inputs that the owner brief does not provide:

- the observing epoch,
- the observatory location,
- the pointing coordinate and its frame and epoch, and
- for LSR, the adopted solar-motion convention.

Astropy documents that even a barycentric or heliocentric radial-velocity
correction requires time and location information (`GS-FRAMEDOC-001`):
<https://docs.astropy.org/en/latest/api/astropy.coordinates.SkyCoord.html>

Every one of those inputs is `TODO(Dennis)` / `NEEDS_REVIEW` in the accepted
control records. Rather than assume a zero correction — which would be a silent
scientific claim — the corresponding stages **fail closed** (`GS-FAILCLOSED-001`):

```python
>>> from galaxy_structure.unavailable import barycentric_correction
>>> barycentric_correction(velocity)
UnavailableStageError: barycentric_correction is unavailable and fails closed. ...
```

The same applies to `heliocentric_correction`, `lsr_correction`,
`earth_motion_correction`, `apply_calibration`, `galactic_radius`, and
`rotation_curve`.

## The Doppler convention is a convention, not a finding

`relativistic` is the documented default for this demonstration
(`GS-DOPPLER-001`), and `radio` and `optical` are also supported. The choice is
recorded in the configuration, in the velocity table header, in the figure title
and caption, and in the manifest.

Stating it clearly, because it is easy to over-read (`GS-METHOD-001`):

- It **does not** answer owner-brief question 13.
- It **does not** establish which scale or formula the historical measurements
  should have used.
- It **does not** validate the historical implementation.
- It **does not** authorise any real-observation scientific claim.

## Zero-velocity and round-trip behaviour

Two properties are asserted by tests for every supported convention:

- a frequency exactly equal to the rest frequency maps to **zero velocity**; and
- frequency → velocity → frequency round trips agree within a **relative
  `1e-12`**, the documented tolerance exported as
  `galaxy_structure.velocity.ROUND_TRIP_RTOL`.
