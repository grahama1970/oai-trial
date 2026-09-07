"""Add one synchronized, reduced-motion-safe emphasis cycle to existing SVG flow."""
from xml.etree import ElementTree as E


def animate_flow(root, stages, edges, offsets):
    assert len(stages) == len(offsets) and len(edges) == len(stages) - 1
    assert offsets == sorted(offsets) and offsets[-1] <= 80
    rules = []
    for i, (stage, start) in enumerate(zip(stages, offsets)):
        name = f'oai-stage-{i}'
        stage.set('class', (stage.get('class', '') + ' ' + name).strip())
        stage.set('data-component', f'flow-stage-{i}')
        rules.append(f'@keyframes {name}{{0%,{start}%{{stroke-width:2}}{start+4}%,{start+12}%{{stroke-width:5}}{start+16}%,100%{{stroke-width:2}}}} .{name}{{animation:{name} 12s linear infinite}}')
    for i, edge in enumerate(edges):
        name = f'oai-edge-{i}'
        edge.set('class', (edge.get('class', '') + ' ' + name).strip())
        rules.append(f'@keyframes {name}{{0%,{offsets[i]+3}%{{stroke-opacity:.25}}{offsets[i+1]}%,100%{{stroke-opacity:1}}}} .{name}{{animation:{name} 12s linear infinite}}')
    style = E.Element('{http://www.w3.org/2000/svg}style')
    style.text = '@media (prefers-reduced-motion: no-preference){' + ''.join(rules) + '}'
    root.append(style)
