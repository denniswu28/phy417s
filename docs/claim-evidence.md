# Claim–evidence registry

Every material public claim this repository makes carries a stable ID and a row
in the table below. A claim that is not registered here must not appear in the
README, the repository description, a figure caption, a commit message, a pull
request, a résumé line, or any other public text.

Allowed classifications:

| Classification | Meaning |
| --- | --- |
| `owner-stated` | Dennis Wu supplied the fact. It is **not** machine-verified. |
| `source-demonstrated` | Established by reading the audited source at the recorded commit. |
| `externally-documented` | Established by a cited primary document. |
| `reproduced` | Established by a command in this repository that anyone can re-run. |
| `planned` | A future intention. Not a description of the present. |
| `NEEDS_REVIEW` | Evidence is missing. The claim is **omitted** from promotional wording. |

Two rules that are not negotiable:

1. A document that merely repeats a claim is not evidence for it.
2. No source, citation, run, result, permission, or approval may be fabricated.
   Where evidence is absent the row says `NEEDS_REVIEW` and the claim is not
   made.

## Owner-supplied facts

These come from Dennis Wu's owner brief in the private control repository
`denniswu28/github-portfolio-rebuild` (`owner-briefs/phy417s.md`). They are
recorded as his statements. Nothing here is machine-verified, and no legal
conclusion is drawn from any of it.

| ID | Claim | Evidence | Classification and limit |
| --- | --- | --- | --- |
| `GS-COURSE-001` | The historical work was a **final project**. | Owner brief, recorded owner statement S10 (2026-08-07). | `owner-stated`. No course document was supplied. |
| `GS-COLLAB-001` | Dennis Wu and Alex Tong were the only project partners, contributed **50/50 to the project overall**, and **collected the measurements together**. Alex Tong consents to being named with that attribution. | Owner brief, recorded owner statements S4, S11, S13. | `owner-stated`, not machine-verifiable. An overall-project and joint-collection boundary only; no per-file or per-task allocation is asserted. |
| `GS-PROV-001` | **Dennis wrote all project code.** | Owner brief, recorded owner statements S5 and S12. | `owner-stated`, not machine-verifiable. Public wording must present this as Dennis's statement, never as machine-proven sole authorship. |
| `GS-INSTRUMENT-001` | The historical measurements used a radio telescope with a **2.1 m aperture**. | Owner brief, recorded owner statement S15. | `owner-stated`. The 2.1 m figure is the **telescope aperture**; the spectral line remains near **21 cm**. No receiver, sensitivity, site, date, configuration, or performance claim follows. |
| `GS-PURPOSE-001` | The project **intent** was to analyse measurements near the 21 cm spectral line to study galactic structure and rotation curves. | Owner brief, recorded owner statement S3. | `owner-stated` **intent only**. Never publishable as an achieved outcome. See `GS-ROTATION-001`. |
| `GS-DATA-001` | Permission covers public posting and redistribution of the historical measured files. | Owner brief, recorded owner statement S14. | `owner-stated`; the **grantor and documentary permission source were not supplied** and remain `NEEDS_REVIEW`. This repository therefore retains **no measured data** regardless of the statement. |
| `GS-LICENSE-001` | Newly written, Dennis-owned code in this repository is licensed **GPL-3.0-or-later**. | Owner brief, recorded owner decision S18; `LICENSE`; `pyproject.toml`. | `owner-stated` licence selection for new code only. See `PROVENANCE.md` and `THIRD_PARTY_NOTICES.md`. No terms are asserted for data, archives, course material, documentation, or third-party assets, and no legal or compatibility conclusion is drawn. |

## Facts about the audited historical source

These describe the repository as it stood at commit
`7faf67b306d6f5f0dad9c848ef1d5136a66c70f0`, before this branch replaced the
tree. They come from the accepted private audit (`audits/phy417s.md`). None of
that source survives in this branch.

| ID | Claim | Evidence | Classification and limit |
| --- | --- | --- | --- |
| `GS-SOURCE-001` | The historical executable path read 19 spectra spanning 1.4194–1.4214 GHz, removed spectral spikes, and wrote cleaned two-column tables. | Accepted audit of `analysis.ipynb` cells 2–3 and `galaxy.zip` at `7faf67b`. | `source-demonstrated`. Correctness, calibration, and authorship are separate and remain unestablished. |
| `GS-SOURCE-002` | In the historical source, `freq2vel`, `cal_rot`, and `vel_correction` were never called by an executable cell, and `vel_correction` had an empty body returning `None`. | Accepted audit of `analysis.ipynb` at `7faf67b`. | `source-demonstrated`. This is the specific failure mode that `galaxy_structure.unavailable` now prevents; see `GS-FAILCLOSED-001`. |
| `GS-UNITS-001` | The historical source carried **two different rest-frequency scales and two different Doppler formulas** for the same symbol. | Accepted audit: `util.py` used `1420.405751768` with a classical expression; `analysis.ipynb` used `1.420405751768e9` with a relativistic expression. | `source-demonstrated`. Which was intended is **`TODO(Dennis)`**, owner-brief question 13, and is **not** answered by this repository. See `GS-VEL-001`. |
| `GS-REPRO-001` | The historical analysis was reproducible. | No dependency manifest, environment, CI, tests, or documented command existed; the executable path depended on untracked inputs and an untracked output directory. | **`NEEDS_REVIEW`** — nothing in the historical source was ever independently reproduced. The claim is **not made**. |

## What this repository demonstrates

Every row below is re-runnable. The commands are in `README.md` and in
`.github/workflows/ci.yml`, and they are the same commands in both places.

| ID | Claim | Evidence | Classification and limit |
| --- | --- | --- | --- |
| `GS-SYN-001` | **Every datum in this repository is synthetic** and is generated by the committed, seeded generator. No measured observation is shipped, read, or reproduced. | `src/galaxy_structure/synthetic.py`; the `synthetic` label enforced by `src/galaxy_structure/spectrum.py`; `tests/test_spectrum.py`, `tests/test_synthetic.py`, `tests/test_demo.py`. | `reproduced`. |
| `GS-DET-001` | Two runs of the same configuration and seed produce **byte-identical** artifacts when both runs happen in the same pinned environment on the same platform. | `tests/test_demo.py::test_two_runs_in_separate_directories_are_byte_identical`; the `diff -r` double-run step in `.github/workflows/ci.yml`, run at the exact head. | `reproduced`, scoped to one pinned environment (`constraints-ci.txt`, CPython 3.12) on one platform. **Cross-platform byte identity is explicitly not claimed** — see `GS-DET-002`. |
| `GS-DET-002` | Artifact bytes **differ between operating systems**, even under identical pins. | Observed directly while preparing this branch. The same commit, configuration, and seed were run under `constraints-ci.txt` on Windows and on the CI platform (`ubuntu-24.04`). Result: exactly **one of 601** amplitude samples differed, by **one representable floating-point step** (`0.06481719480790925` on Windows against `0.06481719480790923` on Linux); the interference-mask record was byte-identical; and both PNGs differed. | `reproduced` as a **limitation**, not a defect. The mechanism is **not established here** — this repository does not determine which operation produced the difference, and asserts no cause. Consequences: the committed figures are the CI platform's bytes, `git diff --exit-code -- docs/figures` is a gate **for that platform**, and running it on another operating system is expected to report a difference that is not drift in this repository's inputs or code. |
| `GS-CLEAN-001` | The cleaner **preserves every unmasked sample bitwise** and **records every sample it altered**. | `src/galaxy_structure/interference.py`; `tests/test_interference.py`. | `reproduced` **on synthetic interference that this package injected**. This is **not** a claim of scientifically validated interference removal or signal preservation on any real observation. |
| `GS-VEL-001` | Frequency-to-velocity conversion requires an **explicit rest-frequency quantity** and an **explicit Doppler convention**, and rejects a bare number, an incompatible unit, or an unknown convention. | `src/galaxy_structure/velocity.py`; `tests/test_velocity.py`. | `reproduced`. This is a **synthetic-demonstration convention only**. It does not answer owner-brief question 13, does not select the historically correct scale or formula, does not validate the historical implementation, and authorises no real-observation scientific claim. |
| `GS-FAILCLOSED-001` | Real-observation calibration, barycentric, heliocentric, LSR, Earth-motion, galactic-radius, and rotation-curve stages **fail closed** with a specific exception naming the absent inputs. Nothing is stubbed, zeroed, or partially returned. | `src/galaxy_structure/unavailable.py`; `tests/test_unavailable.py`. | `reproduced`. |
| `GS-VALID-001` | Public inputs reject non-finite values, empty input, wrong shape, mismatched lengths, non-increasing or non-uniform grids, non-positive frequency, incompatible units, and invalid configuration. | `tests/test_spectrum.py`, `tests/test_config.py`, `tests/test_velocity.py`. | `reproduced`. |
| `GS-PATHS-001` | No committed or generated public artifact contains an absolute runtime path. | `tests/test_demo.py::test_no_artifact_contains_an_absolute_runtime_path`, `::test_manifest_does_not_name_the_output_directory`; `tests/test_plotting.py::test_before_after_figure_carries_no_run_varying_metadata`. | `reproduced`. |
| `GS-FIG-001` | Committed figure `docs/figures/synthetic_spectrum_before_after.png` shows a **synthetic** spectrum before and after deterministic removal of **synthetic** interference that this package injected. | `scripts/regenerate_figures.py`; `docs/figures/figure-provenance.json`; `tests/test_plotting.py`; the drift gate `git diff --exit-code -- docs/figures`. | `reproduced`. Not an observation. No interference-removal performance on real data is claimed. |
| `GS-FIG-002` | Committed figure `docs/figures/synthetic_frequency_velocity_mapping.png` shows the frequency-to-velocity mapping under the stated convention and rest frequency, with **no** observational reference-frame correction applied. | `scripts/regenerate_figures.py`; `docs/figures/figure-provenance.json`; `tests/test_plotting.py`. | `reproduced`. Not an observation. See `GS-FRAME-001`. |
| `GS-FRAME-001` | The velocity coordinate produced here carries **no observational reference frame**: it is not topocentric, geocentric, barycentric, heliocentric, or LSR. | `src/galaxy_structure/velocity.py` (`reference_frame: none-applied`, recorded in every velocity artifact and in the manifest); `tests/test_velocity.py`. | `reproduced`. |

## External reference values and standards

| ID | Claim | Evidence | Classification |
| --- | --- | --- | --- |
| `GS-REST-001` | The rest frequency used by default, **1 420 405 751.768 Hz**, is the recommended hydrogen ground-state hyperfine transition frequency from the NIST hydrogen compilation, quoted there as `1 420 405 751.768(1) Hz`. | <https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=842564> — stated in the introductory text and in Table 1 (hydrogen, `n = 1`, `S1/2`). | `externally-documented`. An **external reference value**, not a result of this project. |
| `GS-DOPPLER-001` | The default Doppler convention is Astropy's relativistic Doppler equivalency. | <https://docs.astropy.org/en/stable/api/astropy.units.doppler_relativistic.html> | `externally-documented`. Selected as a documented convention for this synthetic demonstration. |
| `GS-RNG-001` | Randomness comes from an explicitly seeded `numpy.random.default_rng`; reproducibility holds for a fixed seed within a fixed NumPy version, which is why NumPy is pinned. | <https://numpy.org/doc/stable/reference/random/> | `externally-documented`. |
| `GS-FRAMEDOC-001` | A barycentric or heliocentric radial-velocity correction requires observing time and observatory location information. | <https://docs.astropy.org/en/latest/api/astropy.coordinates.SkyCoord.html> | `externally-documented`. This is why `GS-FAILCLOSED-001` applies rather than a zero correction. |
| `GS-PKG-001` | Project metadata and wheel behaviour follow the PyPA packaging tutorial. | <https://packaging.python.org/en/latest/tutorials/packaging-projects/> | `externally-documented`. |
| `GS-GPLTEXT-001` | `LICENSE` is the official GNU General Public License version 3 text, and the package metadata states `GPL-3.0-or-later`. | <https://www.gnu.org/licenses/gpl-3.0.html>; `LICENSE`; `pyproject.toml`. | `externally-documented` for the text; see `GS-LICENSE-001` for the selection. |

## Prohibited claims — evidence absent

Each row states a claim this project **does not make**. None may appear in the
README, the repository description, a figure caption, a commit message, a
résumé line, a website page, or any other public text, until a rebuilt pipeline
is independently reproduced, validated against a named reference method, and
explicitly approved by Dennis.

| ID | Prohibited claim | Why it is not made |
| --- | --- | --- |
| `GS-ROTATION-001` | Any rotation curve, rotation-velocity value, or curve shape, flatness, turnover, or fit. | **`NEEDS_REVIEW`.** No rotation curve is produced, plotted, fitted, or validated anywhere. `galaxy_structure.unavailable.rotation_curve` fails closed. |
| `GS-GALSTRUCT-001` | Any galactic-structure result: spiral-arm identification, arm tangent, distance, galactic radius, mass, mass distribution, or dark-matter inference. | **`NEEDS_REVIEW`.** No galactic-structure quantity is computed. |
| `GS-CALACC-001` | Any calibration accuracy, gain, system temperature, brightness temperature, bandpass quality, or instrument-performance figure. | **`NEEDS_REVIEW`.** No calibration is applied; `apply_calibration` fails closed. |
| `GS-UNCERT-001` | Any uncertainty, error bar, confidence interval, significance, precision, repeatability, or agreement-with-literature statement. | **`NEEDS_REVIEW`.** No uncertainty of any kind is computed. |
| `GS-DETECT-001` | Any statement that this project detects the 21 cm line or resolves galactic kinematics. | **`NEEDS_REVIEW`.** Every spectrum here is synthetic; a synthetic feature is not a detection. |
| `GS-METHOD-001` | That the Doppler convention or rest frequency selected here is the historically correct choice for the measured files. | **`NEEDS_REVIEW`.** Owner-brief question 13 is unanswered. See `GS-VEL-001` and `GS-UNITS-001`. |
| `GS-CONSUMER-001` | That this repository has, or has no, external downstream consumers. | **`NEEDS_REVIEW`.** External clones, forks, links, citations, and mirrors are not observable from inside the repository, and absence of a record is not evidence of absence. |
| `GS-SCANSAFE-001` | That the repository's history is free of confidential, personal, institutional, or third-party material. | **`NEEDS_REVIEW`.** Redacted pattern scans reported zero pattern matches within their recorded scope. Zero findings means no pattern match; it establishes nothing further and grants no redistribution right. Excluded blobs remain reachable in the pre-existing history. |
