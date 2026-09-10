#!/usr/bin/env python3
"""Generate a synthetic mixed-format input bundle for the anonymization trial.

Thin CLI over anonymization_trial.fixture.generate_fixture. Exists so live
evals can generate real-format input bundles without referencing fixtures/
paths (the agentic-evals runner structurally disqualifies those commands).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from anonymization_trial.fixture import generate_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="input bundle directory to create")
    parser.add_argument("--records", type=int, default=25, help="records per format")
    args = parser.parse_args()
    generate_fixture(args.target, args.records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
