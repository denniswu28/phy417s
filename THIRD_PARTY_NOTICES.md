# Third-party notices

This file lists the licence of the newly written code, the historical notice
this repository previously carried, and the actual runtime dependencies.

**No legal or licence-compatibility conclusion is drawn anywhere in this file.**
It records facts and notices. Questions of compatibility, obligation, and scope
are outside what this repository establishes, and nothing here is legal advice.

## 1. Newly written code in this repository

Licensed **GPL-3.0-or-later** (`GS-LICENSE-001`).

- [`LICENSE`](LICENSE) contains the official GNU General Public License version
  3 text from <https://www.gnu.org/licenses/gpl-3.0.html>.
- `pyproject.toml` declares the SPDX expression `GPL-3.0-or-later`, so the
  "or later" option is stated in the package metadata rather than left to the
  file alone.

This selection is Dennis Wu's, recorded as owner decision S18 in the private
control repository. It covers **newly written, Dennis-owned code only**. It
asserts no terms for measured data, archives, course material, documentation,
photographs, or third-party assets, none of which is present here.

## 2. The historical MIT notice — a preserved fact, not a current grant

This is recorded because the fact must not be silently dropped, and it is kept
separate from section 1 because the two are different things.

At the audited source commit `7faf67b306d6f5f0dad9c848ef1d5136a66c70f0`, the
repository's root `LICENSE` file contained an **MIT notice, copyright (c) 2023
Dennis Wu**. This branch replaced that file, as authorised by the owner-approved
manifest. The historical notice itself is reproduced here so that it remains on
the record:

```text
MIT License

Copyright (c) 2023 Dennis Wu
```

Three separate statements, which must not be collapsed into one:

1. **The notice existed.** An MIT notice naming Dennis Wu and dated 2023 was
   present at the repository root at that commit. That is all the evidence
   establishes about it.
2. **Its scope was never established.** It was an MIT notice at a repository
   root. It is **not** evidence that MIT terms covered the measured spectra, the
   calibration files, either archive, notebook outputs, course-supplied
   material, photographs, third-party assets, or code that did not yet exist.
3. **No code it applied to survives here.** This branch retains no legacy code
   or notebook cell (see [`PROVENANCE.md`](PROVENANCE.md)). The historical file
   remains reachable in the repository's pre-existing commits, which this work
   does not alter.

## 3. Runtime dependencies

Declared in `pyproject.toml` and pinned for verification in
`constraints-ci.txt`. Each is installed from PyPI; each carries its own licence
and notices in its own distribution, which are not reproduced here.

| Dependency | Used for | Project home |
| --- | --- | --- |
| NumPy | Arrays, the seeded random generator, and the median filter | <https://numpy.org/> |
| Astropy | Units, quantities, and the Doppler equivalencies | <https://www.astropy.org/> |
| Matplotlib | Deterministic PNG figure rendering via the Agg backend | <https://matplotlib.org/> |

Their own transitive dependencies — including `astropy-iers-data`, `contourpy`,
`cycler`, `fonttools`, `kiwisolver`, `packaging`, `pillow`, `pyerfa`,
`pyparsing`, `python-dateutil`, `PyYAML`, and `six` — are pinned in
`constraints-ci.txt` for reproducibility. They are installed by the package
manager from their own distributions and carry their own licences and notices.

## 4. Verification tooling

Used to check this repository, not distributed with it: `build`, `ruff`,
`pytest`, and their dependencies, all pinned in `constraints-ci.txt`.

## 5. Fonts in the committed figures

The committed PNGs are rendered with **DejaVu Sans**, the font matplotlib ships
and uses by default. No font file is vendored into this repository; the figures
contain rasterised glyphs only, and matplotlib's own distribution carries the
font's licence and notices.

## 6. What is not here

No measured data, no archives, no course material, no photographs, no
third-party images, and no vendor or instrument interface code is present in
this repository, so no notice is recorded for any of them.
