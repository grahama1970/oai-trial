# Theme handoff — candidate authoring

The supplied grahama.co tokens are applied unchanged in deck.json: Fraunces headings, system-ui prose (export maps to Arial), warm dark canvas, brass accent, opaque #211917 header fill and an independent 0.1 image opacity.

`assets/house-band-texture.png` is the ACTUAL supplied PNG decoded byte-for-byte, not a translucent rectangle or replacement image. SHA-256: aec0408102d6284bf47e4d57d7924c395bc9912ca4ce1620a25c9379c3417542. The current supported consumer automatically adds its canonical house-band texture at this opacity. Do not add a second freeform header image or footer over compiler chrome.

The consumer's theme source was inspected at the returned immutable version:
https://github.com/grahama1970/agent-skills/blob/8bca242a8c77dfc3cfd1d4d7c61db115b0ab7dab/skills/pitchdeck/src/pitchdeck/theme_style.py
This was compatibility inspection only, not renderer execution or a change to the implementation baseline.

No font files are bundled. Native `el:title` uses the supported heading-font mapping. Native reading prose uses the body token. Machine identifiers, code plates and diagram IDs use an explicit Consolas/Courier New/monospace font declaration in self-contained SVGs because the supplied FreeformElement schema does not support a per-element font-family override. SVG internals remain image content, not natively editable PowerPoint objects.

Actual browser/PPTX font resolution, wrapping, header compositing and footer placement require the local compiler and human preview. This package neither runs nor claims those checks. No sponsor/distribution markings from reference decks are copied.
