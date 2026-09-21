#!/usr/bin/env python3
"""Adversarial image/PDF campaign for the optional multimodal release path."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - campaign constructs fixed executable argv
        argv, capture_output=True, text=True, timeout=300, check=False
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if (
        not shutil.which("tesseract")
        or not shutil.which("pdftoppm")
        or not shutil.which("pdftotext")
    ):
        raise SystemExit("multimodal battle tools unavailable")
    from PIL import Image, ImageDraw, ImageFont

    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not font_path.exists():
        raise SystemExit("multimodal battle font unavailable")
    sensitive = "alice@example.com"
    with tempfile.TemporaryDirectory(prefix="multimodal-battle-") as directory:
        root = Path(directory)
        image = Image.new("RGB", (900, 180), "white")
        ImageDraw.Draw(image).text(
            (30, 60),
            f"Contact {sensitive} today",
            fill="black",
            font=ImageFont.truetype(str(font_path), 36),
        )
        sources = {"image": root / "input.png", "pdf-hidden-layer": root / "input.pdf"}
        image.save(sources["image"])
        image.save(sources["pdf-hidden-layer"], "PDF", resolution=150)
        policy = root / "policy.json"
        policy.write_text(
            json.dumps(
                {
                    "version": 1,
                    "sensitive_values": [
                        {
                            "rule_id": "email",
                            "subject_id": "p1",
                            "type": "email",
                            "value": sensitive,
                        }
                    ],
                    "protected_values": [],
                }
            ),
            encoding="utf-8",
        )
        cases = []
        for name, source in sources.items():
            suffix = source.suffix
            output = root / f"output-{name}{suffix}"
            receipt = root / f"receipt-{name}.json"
            completed = _run(
                [
                    sys.executable,
                    "-m",
                    "anonymization_trial",
                    "redact-document",
                    "--input",
                    str(source),
                    "--policy",
                    str(policy),
                    "--output",
                    str(output),
                    "--receipt",
                    str(receipt),
                ]
            )
            visual = _run(["tesseract", str(output), "stdout"])
            hidden = ""
            if suffix == ".pdf":
                hidden_result = _run(["pdftotext", str(output), "-"])
                hidden = hidden_result.stdout
            passed = (
                completed.returncode == 0
                and output.is_file()
                and sensitive.casefold() not in visual.stdout.casefold()
                and sensitive.casefold() not in hidden.casefold()
                and json.loads(receipt.read_text(encoding="utf-8"))["verification_passed"] is True
            )
            cases.append({"case": name, "verdict": "BLUE_WIN" if passed else "RED_WIN"})
        red_wins = sum(case["verdict"] == "RED_WIN" for case in cases)
        result = {
            "schema": "multimodal_battle_receipt.v1",
            "status": "PASS" if red_wins == 0 else "FAIL",
            "red_wins": red_wins,
            "cases": cases,
            "assertions": [
                "post-redaction OCR contains no policy literal",
                "PDF hidden text layer contains no policy literal",
            ],
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, sort_keys=True))
        return 0 if red_wins == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
