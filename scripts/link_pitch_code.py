#!/usr/bin/env python3
"""Add explicit HTTPS code links to compiler-emitted CODE / EVIDENCE text.

Preserves all other PPTX parts. Does not embed executable macros or local launch
URIs. Re-run pitchdeck verify and render on the linked output, not the input.
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P = "http://schemas.openxmlformats.org/package/2006/relationships"


def parse_xml(data: bytes):
    text = data.decode("utf-8")
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise ValueError("DTD/entity declarations are not allowed in presentation XML")
    return ET.fromstring(text)  # noqa: S314 (UTF-8 only, DTD/entities rejected above)


def link(source: Path, output: Path, index: Path) -> None:
    if source.resolve() == output.resolve():
        raise ValueError("input and linked output must be distinct")
    links = json.loads(index.read_text())["slides"]
    with ZipFile(source) as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    # Keep link contrast on the dark slides; office viewers use theme hyperlink
    # colors even when the source text run already carries an explicit color.
    for name in list(parts):
        if name.startswith("ppt/theme/") and name.endswith(".xml"):
            theme = parse_xml(parts[name])
            for tag in ("hlink", "folHlink"):
                node = theme.find(f".//{{{A}}}{tag}")
                if node is not None:
                    node.clear()
                    ET.SubElement(node, f"{{{A}}}srgbClr", {"val": "22D3EE"})
            parts[name] = ET.tostring(theme, encoding="utf-8", xml_declaration=True)
    for number, item in enumerate(links.values(), 1):
        url = item["url"]
        if not url.startswith("https://github.com/grahama1970/oai-trial/blob/"):
            raise ValueError("only commit-pinned repository links are allowed")
        part = f"ppt/slides/slide{number}.xml"
        rel = f"ppt/slides/_rels/slide{number}.xml.rels"
        tree = parse_xml(parts[part])
        relationships = parse_xml(parts[rel])
        identity = "pitchEvidence"
        ET.SubElement(
            relationships,
            f"{{{P}}}Relationship",
            {
                "Id": identity,
                "Type": R + "/hyperlink",
                "Target": url,
                "TargetMode": "External",
            },
        )
        matches = 0
        for run in tree.iter(f"{{{A}}}r"):
            if run.findtext(f"{{{A}}}t", "") == "CODE / EVIDENCE":
                props = run.find(f"{{{A}}}rPr")
                if props is None:
                    props = ET.Element(f"{{{A}}}rPr")
                    run.insert(0, props)
                ET.SubElement(props, f"{{{A}}}hlinkClick", {f"{{{R}}}id": identity})
                matches += 1
        if matches != 1:
            raise ValueError(f"slide {number}: expected one code link, found {matches}")
        parts[part] = ET.tostring(tree, encoding="utf-8", xml_declaration=True)
        parts[rel] = ET.tostring(relationships, encoding="utf-8", xml_declaration=True)
    with ZipFile(output, "w") as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
    print(f"Linked {len(links)} source references; no executable hyperlinks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--index", type=Path, default=Path("docs/pitch/oai-trial/qa/code_links.json")
    )
    args = parser.parse_args()
    link(args.source, args.output, args.index)
