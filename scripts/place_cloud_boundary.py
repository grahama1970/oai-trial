"""Rebuild the retained cloud diagram from its source and absolute geometry grid."""
import json
from pathlib import Path
from xml.etree import ElementTree as E
from svg_flow_animation import animate_flow

B = Path(__file__).resolve().parents[1] / 'docs/pitch/oai-trial/reorganized/assets'
NS = 'http://www.w3.org/2000/svg'
E.register_namespace('', NS)
grid = json.loads((B / 'cloud-boundaries.grid.json').read_text())
root = E.parse(B / 'cloud-boundaries.source.svg').getroot()
def node(tag, **attrs):
    return E.Element(f'{{{NS}}}{tag}', {k.replace('_', '-'): str(v) for k,v in attrs.items()})
old_x = {45:'intake',340:'workers',645:'verify',985:'publish',600:'quarantine'}
centers = {170:170,470:495,770:820,1180:1197.5,760:820,1178:1197.5,322:332.5}
for e in list(root):
    kind=e.tag.split('}')[-1]
    if kind in ['line','polygon','path']:root.remove(e);continue
    if kind=='rect' and e.get('x'):
        x=float(e.get('x'));n=grid['work_boundary'] if x==20 else grid['nodes'][old_x[x]]
        for k,v in [('x',n['x']),('y',n['y']),('width',n['w']),('height',n['h'])]:e.set(k,str(v))
        if x in old_x:e.set('id',old_x[x]);e.set('data-component',old_x[x])
    if kind=='text':
        x=float(e.get('x'))
        if x in centers:
            e.set('x',str(centers[x]))
            for span in e:span.set('x',str(centers[x]))
defs=node('defs')
for id,color in [('flow-arrow','#e2ac62'),('failure-arrow','#d1703c')]:
    marker=node('marker',id=id,markerWidth=10,markerHeight=10,refX=9,refY=5,orient='auto',markerUnits='userSpaceOnUse');marker.append(node('path',d='M0 0 L9 5 L0 10 Z',fill=color));defs.append(marker)
root.insert(3,defs)
def edge(d,failure=False):root.append(node('path',d=d,fill='none',stroke='#d1703c' if failure else '#e2ac62',stroke_width=3,marker_end='url(#failure-arrow)' if failure else 'url(#flow-arrow)'))
n=grid['nodes']
for a,b in [('intake','workers'),('workers','verify'),('verify','publish')]:
    src,dst=n[a],n[b];y=src['y']+src['h']/2;edge(f'M {src["x"]+src["w"]+4} {y} H {dst["x"]-6}')
v,q=n['verify'],n['quarantine'];cx=v['x']+v['w']/2;assert cx==q['x']+q['w']/2;edge(f'M {cx} {v["y"]+v["h"]+4} V {q["y"]-6}',True)
a,w=n['intake'],n['workers'];edge(f'M {w["x"]+w["w"]/2} {w["y"]+w["h"]+4} V {grid["retry_y"]} H {a["x"]+a["w"]/2} V {a["y"]+a["h"]+6}')
root.append(node('line',x1=grid['publication_boundary_x'],x2=grid['publication_boundary_x'],y1=50,y2=475,stroke='#e2ac62',stroke_width=2,stroke_dasharray='8 6'))
animate_flow(root, [root.find(f'.//{{{NS}}}rect[@id="{id}"]') for id in ['intake','workers','verify','publish']], [e for e in root if e.tag.endswith('path')][:3], [0,20,40,60])
E.ElementTree(root).write(B/'cloud-boundaries.svg',encoding='unicode')
print('Cloud diagram rebuilt: Dispatch + workers width340; heading32; connectors reanchored.')
