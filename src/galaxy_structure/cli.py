"""Command-line interface.

    galaxy-structure run-demo --output-dir OUTPUT_DIR --seed 20260807

Every failure is reported on stderr with a non-zero exit status. Nothing is
retried, defaulted, or partially written on error.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .config import default_config, load_config
from .demo import ARTIFACT_PATHS, MANIFEST_NAME, run_demo
from .errors import GalaxyStructureError

_EPILOG = (
    "Every artifact this command writes is synthetic and is labelled as such. "
    "Nothing it produces is an observation, and it computes no rotation curve, "
    "calibration accuracy, uncertainty, or other scientific result."
)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="galaxy-structure",
        description="Deterministic, synthetic-only 21 cm spectrum analysis demonstration.",
        epilog=_EPILOG,
    )
    parser.add_argument("--version", action="version", version=f"galaxy-structure {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)
    demo = subparsers.add_parser(
        "run-demo",
        help="Generate the synthetic demonstration artifacts.",
        description="Generate the synthetic demonstration artifacts.",
        epilog=_EPILOG,
    )
    demo.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory to write the synthetic artifacts into. Created if absent.",
    )
    demo.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the configured random seed. Must not be negative.",
    )
    demo.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Configuration file. Defaults to the built-in configuration, of which "
        "config/demo.json is the documented copy.",
    )
    return parser


def _run_demo_command(arguments: argparse.Namespace) -> int:
    config = default_config() if arguments.config is None else load_config(arguments.config)
    if arguments.seed is not None:
        config = config.with_seed(arguments.seed)

    run = run_demo(config, arguments.output_dir)

    print(f"galaxy-structure {__version__}: wrote {len(ARTIFACT_PATHS)} synthetic artifacts.")
    for key in sorted(ARTIFACT_PATHS):
        print(f"  {ARTIFACT_PATHS[key]}")
    print(f"  {MANIFEST_NAME}")
    print(f"seed: {run.config.seed}")
    print(
        "Every artifact above is synthetic and is not an observation. No rotation curve, "
        "calibration accuracy, uncertainty, or reference-frame correction is produced."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns the process exit status."""
    parser = build_parser()
    arguments = parser.parse_args(argv)

    try:
        if arguments.command == "run-demo":
            return _run_demo_command(arguments)
    except GalaxyStructureError as error:
        print(f"galaxy-structure: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"galaxy-structure: {error}", file=sys.stderr)
        return 1

    parser.error(f"unknown command: {arguments.command!r}")  # pragma: no cover - argparse guards


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
