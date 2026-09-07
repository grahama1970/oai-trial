"""Read back the native document, emitted browser payload and actual PPTX.

Structural/content checks only: not PowerPoint playback or human visual approval.
"""
import json
from pathlib import Path
import urllib.request
from xml.etree import ElementTree as E
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'docs/pitch/oai-trial/reorganized'
def unique(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError('duplicate JSON key: '+k)
        result[k]=v
    return result
def walk(elements):
    for element in elements or []:
        yield element
        yield from walk(element.get('children'))
doc=json.loads((B/'deck.document.json').read_text(),object_pairs_hook=unique,parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
assert doc['schema']=='pitchdeck.deck_document.v1' and len(doc['slides'])==32
with urllib.request.urlopen('http://127.0.0.1:3016/oai-trial-current/deck.data.json',timeout=10) as response:ui=json.load(response)
assert ui['source']=='pitchdeck.deck_document.v1'
assert not ui['validation_gaps']
assert [s['id'] for s in doc['slides']]==[s['id'] for s in ui['slides']]
for src,out in zip(doc['slides'],ui['slides']):
    expected={e['id']:e for e in walk(src['elements'])};actual={e['id']:e for e in walk(out['elements'])}
    assert expected.keys()==actual.keys(),src['id']
    assert src['notes']==out['notes'] and len(src['animations'])==len(out['animations'])
    assert all(all(b.get(k)==v for k,v in a.items()) for a,b in zip(src['animations'],out['animations']))
    for id,e in expected.items():
        if e['kind']=='text':assert e['text']==actual[id]['text'],id
        if e['kind']=='icon':assert actual[id]['icon_svg'] and '#000' not in actual[id]['icon_svg']
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
icons=checks=0
with ZipFile('/mnt/storage12tb/oai-trial/native-pitchdeck/oai-trial-current.pptx') as archive:
    for i,s in enumerate(doc['slides'],1):
        root=E.fromstring(archive.read(f'ppt/slides/slide{i}.xml'))
        text=' '.join(' '.join((n.text or '').split()) for n in root.findall('.//a:t',ns))
        for e in walk(s['elements']):
            if e['kind']=='text':assert ' '.join(e['text'].split()) in text,(s['id'],e['id'])
        assert root.find('p:transition/p:fade',ns) is not None
        if s['animations']:assert root.find('p:timing',ns) is not None
        for group in root.findall('.//p:grpSp',ns):
            props=group.find('p:nvGrpSpPr/p:cNvPr',ns)
            if props is not None and props.get('name')=='el:header-topic-icon':
                icons+=1;assert {n.get('val').upper() for n in group.findall('.//a:srgbClr',ns)}=={'F2EADC'}
        for shape in root.findall('.//p:sp',ns):
            if ''.join(n.text or '' for n in shape.findall('.//a:t',ns))=='✓':
                checks+=1;assert 'A99787' in {n.get('val').upper() for n in shape.findall('.//a:srgbClr',ns)}
assert icons==32 and checks==4
assert sum(m['duration_minutes'] for m in json.loads((B/'slide-map.json').read_text()) if m['counts_toward_prepared_time'])==30
print('CANONICAL_READBACK_PASS: complete32-slide JSON; no dropped UI elements; notes/builds preserved;32 cream native header icons;4 neutral checkmarks; native timing present. Playback not implied.')
