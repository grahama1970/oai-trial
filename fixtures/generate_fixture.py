from __future__ import annotations

import argparse
from pathlib import Path

from anonymization_trial.fixture import generate_fixture


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a synthetic mixed-format input bundle")
    parser.add_argument("target", type=Path)
    parser.add_argument("--records", type=int, default=25)
    args = parser.parse_args()
    generate_fixture(args.target, args.records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
