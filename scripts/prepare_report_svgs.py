"""Bounded intake of the two supplied WebGPT SVGs; retain their panel structure.

Corrects the evidence sequence to runtime publication followed by an external
qualification-only readback. It never makes readback a runtime release gate.
"""
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
from svg_flow_animation import animate_flow

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'docs/pitch/oai-trial/reorganized/assets/report-source'
OUTPUT = ROOT / 'docs/pitch/oai-trial/reorganized/assets'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

def element(tag, **attrs):
    return ET.Element(f'{{{NS}}}{tag}', {k: str(v) for k, v in attrs.items()})

for name, expected, destination in [
    ('oai_trial_core_architecture.svg', 'eb8eb81087b81ddc73a25d55946749ef69255e215aae425f3dcea9e9198b9672', 'report-core.svg'),
    ('oai_trial_evidence_boundaries.svg', '4b4ed4019fba97b0252bab0c25a5b94ba766f047422b4790a0f87e23be28bdb6', 'report-evidence.svg'),
]:
    data = (INPUT / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected, 'Unexpected external SVG revision'
    root = ET.fromstring(data)
    core = 'core_architecture' in name
    title = element('title', id='diagram-title'); title.text = 'Policy-bounded runtime' if core else 'Runtime and separate qualification evidence'
    desc = element('desc', id='diagram-description'); desc.text = ('Human policy declarations enter compilation, transformation, verification and publication. Broader privacy properties are not established.' if core else 'Runtime transforms, verifies and publishes. A separate qualification harness reads published fixture outputs afterward; it is not a runtime publication gate.')
    root.set('role', 'img'); root.set('aria-labelledby', 'diagram-title diagram-description')
    root.insert(0, title); root.insert(1, desc)
    root.insert(2, element('rect', width=root.get('width'), height=root.get('height'), fill='#0c0908'))
    panels = [n for n in root if n.tag.endswith('rect') and n.get('rx')]
    for node in root.iter():
        if node.get('fill') == '#fff': node.set('fill', '#181211')
        if node.get('fill') == '#111': node.set('fill', '#e2ac62' if node.tag.endswith('path') else '#ece2d3')
        if node.get('stroke') == '#111': node.set('stroke', '#e2ac62')
    if core:
        assert len(panels) == 6
        width, gap = 220, 45
        margin = (1400 - 5 * width - 4 * gap) / 2
        labels = [('Human / policy', 'Declared literals'), ('Compile policy', 'Literal conflicts'), ('Transform', 'Original spans'), ('Verify', 'Types + locations'), ('Publish', 'report.json last')]
        for i, panel in enumerate(panels[:5]): panel.set('x', str(margin + i * (width + gap)))
        for node in list(root):
            if node.tag.endswith('text'):
                y = float(node.get('y')); x = float(node.get('x'))
                if y in [42, 70, 227, 248, 547]: root.remove(node); continue
                if y in [178, 206]:
                    i = round((x - 150) / 265); node.set('x', str(margin + i * (width + gap) + width / 2))
                    node.text = labels[i][0 if y == 178 else 1]; node.set('y', '220' if y == 178 else '260')
                    node.set('font-size', '24' if y == 178 else '20'); node.set('dominant-baseline', 'central')
                elif y == 498: node.text = 'Not established'; node.set('font-size', '24')
                elif y == 526: node.text = 'Completeness · personhood · anonymity · linkage'; node.set('font-size', '22')
            elif node.tag.endswith('line'):
                if node.get('y1') != node.get('y2'): root.remove(node); continue
                i = round((float(node.get('x1')) - 260) / 265)
                node.set('x1', str(margin + i * (width + gap) + width + 4))
                node.set('x2', str(margin + (i + 1) * (width + gap) - 6))
    else:
        assert len(panels) == 4
        labels = [('Transform', 'Declared replacements'), ('Runtime verifier', 'Fresh contract checks'), ('Publish', 'report.json last'), ('Separate fixture readback', 'Known-fixture outputs')]
        for node in list(root):
            if node.tag.endswith('text'):
                y = float(node.get('y'))
                if y in [70, 207, 337, 467, 597]: root.remove(node); continue
                if y == 42: node.text = 'Evidence boundaries'
                elif y == 675: node.text = 'Not general privacy approval'
                else:
                    i = round((y - 158) / 130); detail = y == 186 + i * 130
                    node.text = labels[i][int(detail)]; node.set('font-size', '24' if not detail else '22')
            elif node.tag.endswith('line'):
                node.set('y1', str(float(node.get('y1')) + 4)); node.set('y2', str(float(node.get('y2')) - 6))
                if float(node.get('y1')) > 490: node.set('stroke-dasharray', '6 4')
        note = element('text', x=740, y=510, fill='#a99787', **{'font-family':'Arial, sans-serif', 'font-size':17}); note.text='Qualification only'; root.append(note)
    assert len(root.findall(f'.//{{{NS}}}text')) <= 12
    flow_edges = [e for e in root if e.tag.endswith('line')]
    animate_flow(root, panels[:5] if core else panels, flow_edges, [0, 15, 30, 45, 60] if core else [0, 20, 40, 65])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(OUTPUT / destination, encoding='unicode')
    print(destination)
