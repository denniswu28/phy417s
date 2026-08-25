"""galaxy-structure: a deterministic, synthetic-only 21 cm spectrum analysis demonstration.

This package generates, perturbs, cleans, and converts **synthetic** spectra. It
contains no measured observation, produces no rotation curve, and asserts no
scientific result. See ``docs/claim-evidence.md`` for the claim registry and
``docs/limitations.md`` for the boundary this package deliberately does not cross.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

try:
    __version__ = _version("galaxy-structure")
except PackageNotFoundError:  # pragma: no cover - only reachable in an uninstalled tree
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
