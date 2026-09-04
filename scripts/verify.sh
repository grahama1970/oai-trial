#!/usr/bin/env bash
# Local readiness gate: build the package, run the unittest suite, run the demo,
# and run + verify a fixture-generated corpus. Exits non-zero on any failure.
set -euo pipefail

cd "$(dirname "$0")/.."

PY="${PYTHON:-python3.12}"
VENV=".venv"

if [ ! -x "$VENV/bin/python" ]; then
  "$PY" -m venv "$VENV"
fi
"$VENV/bin/pip" install -q -e .

echo "== unittest =="
"$VENV/bin/python" -m unittest discover -s tests

echo "== demo =="
"$VENV/bin/anonymization-trial" demo | grep -q '"demo": "success"'

echo "== run over fixture =="
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
"$VENV/bin/python" fixtures/generate_fixture.py "$work/input" --records 200
"$VENV/bin/anonymization-trial" run --input "$work/input" --output "$work/output"
test -f "$work/output/report.json"
python3 -c "import json,sys; r=json.load(open('$work/output/report.json')); sys.exit(0 if r.get('verification_passed') else 1)"

echo "Result: PASS"
