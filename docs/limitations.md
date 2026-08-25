# Limitations

This page records what this repository does **not** do and does **not** claim.
The absence of a scientific result is documented here deliberately rather than
left for a reader to infer.

Claim IDs refer to [`claim-evidence.md`](claim-evidence.md).

## 1. There is no measured data here

This repository contains **no measured observation** — no spectra, no
calibration files, no archives (`GS-SYN-001`).

Dennis states that permission covers public posting and redistribution of the
historical measured files (`GS-DATA-001`). The grantor and the documentary
permission source were not supplied and remain `NEEDS_REVIEW`, so this
implementation withholds all of it regardless. Reintroducing any measured file
requires a separate evidence review and separate owner approval at its own gate;
it is not something this branch decides.

## 2. There is no scientific result here

None of the following is produced, plotted, fitted, validated, or claimed:

| Not claimed | ID |
| --- | --- |
| Any rotation curve, rotation velocity, or curve shape, flatness, turnover, or fit | `GS-ROTATION-001` |
| Any galactic-structure result: spiral arms, distance, galactic radius, mass, dark matter | `GS-GALSTRUCT-001` |
| Any calibration accuracy, gain, system temperature, brightness temperature, or bandpass quality | `GS-CALACC-001` |
| Any uncertainty, error bar, confidence interval, significance, precision, or literature agreement | `GS-UNCERT-001` |
| Any detection of the 21 cm line, or resolution of galactic kinematics | `GS-DETECT-001` |

The owner-stated project intent — analysing measurements near the 21 cm line to
study galactic structure and rotation curves — is recorded as **intent**
(`GS-PURPOSE-001`), never as an achieved outcome. The accepted private audit
records that the historical source produced no rotation curve and no
galactic-structure quantity.

A synthetic emission-like feature in a synthetic spectrum is **not** a detection
of anything.

## 3. Stages that are deliberately absent

These exist as names and fail closed with a specific exception naming the
missing inputs (`GS-FAILCLOSED-001`):

`apply_calibration`, `barycentric_correction`, `heliocentric_correction`,
`lsr_correction`, `earth_motion_correction`, `galactic_radius`,
`rotation_curve`.

They are absent because the evidence they need is absent — the observing epoch,
the observatory location, the pointing coordinate and its frame, the calibration
procedure, the meaning of the recorded amplitude, and a named reference method
are all `TODO(Dennis)` / `NEEDS_REVIEW`. They are not absent because they are
hard. Adding a zero correction, a stub, or a best-effort partial result would be
a silent scientific claim, so none is offered and there is no "approximate"
mode.

## 4. The cleaner's limits

`GS-CLEAN-001` is a claim about **software behaviour on synthetic interference
that this package injected**. It is not a claim about real radio-frequency
interference.

Specifically:

- a running median **follows** any feature occupying at least half of its
  window, so such a feature cannot be flagged — a test asserts this limitation
  rather than hiding it;
- when the robust scatter estimate is exactly zero the cleaner flags nothing,
  rather than treating ordinary curvature as interference;
- the strategy has not been evaluated against real interference, against any
  alternative method, or for its effect on a real astronomical signal; and
- no false-positive or false-negative rate is characterised, because
  characterising one would require data this repository does not have.

## 5. The conversion convention is not a finding

The Doppler convention and rest frequency are a **synthetic-demonstration
convention** (`GS-VEL-001`, `GS-METHOD-001`). They do not answer owner-brief
question 13, do not establish the historically correct choice for the measured
files, and do not validate the legacy implementation whose two conflicting
rest-frequency scales the audit records (`GS-UNITS-001`).

## 6. Determinism is scoped to one pinned environment on one platform

`GS-DET-001` holds **within the pinned environment of `constraints-ci.txt`, on
Python 3.12, on a single platform**. Repeated runs there are byte-identical, and
CI proves it at the exact head by running the demo twice into clean directories
and comparing with `diff -r`.

**Across operating systems, byte identity does not hold, and is not claimed**
(`GS-DET-002`). This was measured, not assumed. The same commit, configuration
and seed were run under the same pins on Windows and on the CI platform:

- exactly **one of 601** amplitude samples differed, by **one representable
  floating-point step** — `0.06481719480790925` against `0.06481719480790923`;
- the interference-mask record was **byte-identical**, so the seeded random
  stream and every cleaning decision agreed; and
- both PNGs differed.

This repository does **not** establish which operation produced that difference
and asserts no cause for it.

What follows from it, practically:

- The PNGs committed in `docs/figures/` are the bytes produced by the **CI
  platform**, which is where the drift gate is evaluated. Running
  `python scripts/regenerate_figures.py && git diff --exit-code -- docs/figures`
  on a different operating system is expected to report a difference. That
  difference is a platform artifact, not drift in this repository's inputs,
  configuration, or code.
- NumPy guarantees stream reproducibility for a fixed seed within a fixed
  version, which is why NumPy is pinned (`GS-RNG-001`). That guarantee covers
  the random stream, which is exactly the part that did agree.
- PNG bytes additionally depend on the exact matplotlib, Pillow, and font stack,
  which is why both are pinned and the committed figures are generated in the
  same environment CI verifies them in.
- The run manifest records the Python and package versions, so an environment
  mismatch is visible rather than silent.

## 7. What the history still contains

This branch replaces the repository's **current tree**. It performs **no history
operation** — no rewrite, no force-push, no ref deletion.

Every path this branch removes therefore remains reachable in the pre-existing
commits, as does the pre-existing commit-author metadata. A pattern scan
reporting zero findings means no pattern matched; it does not establish that the
history is free of confidential, personal, institutional, or third-party
material, and it grants no redistribution right (`GS-SCANSAFE-001`).

A separately planned history remediation is tracked in the private control
repository. It is out of scope here and is not authorised by this work.

## 8. What is unknown about downstream use

Whether anything outside this repository depends on it is **not observable from
inside it** (`GS-CONSUMER-001`). External clones, forks, hard-coded links,
citations, course submissions, and mirrors cannot be enumerated here. Absence of
a record is not evidence of absence of use.

## 9. Owner-stated facts are not machine-verified

`GS-COURSE-001`, `GS-COLLAB-001`, `GS-PROV-001`, `GS-INSTRUMENT-001`,
`GS-PURPOSE-001`, and `GS-DATA-001` are Dennis Wu's statements, recorded as
such. Repository ownership, commit metadata, and file contents cannot establish
authorship, collaboration boundaries, instrument parameters, or redistribution
rights, and this repository does not claim they do.
