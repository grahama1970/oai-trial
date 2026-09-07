"""Check the research/reuse narrative in sources and actual emitted artifacts.

This checks text, ordering, timing and artifact identity—not visual approval,
paper reproduction, research chronology, or runtime privacy correctness.
"""
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'docs/pitch/oai-trial/reorganized'
PPTX = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/mnt/storage12tb/oai-trial/native-pitchdeck/oai-trial-current.pptx')
deck = json.loads((BUNDLE / 'deck.public.yaml').read_text())
slides = deck['slides']
ids = [s['id'] for s in slides]
assert ids[6:8] == ['r06a-research-reuse', 'r06b-research-adoption']
assert ids[0] == 'r01-toc' and ids[-1] == 'r30-thank-you'
assert ids.index('r23-answer-scale') + 1 == ids.index('r24-security-evals')
assert sum(m['duration_minutes'] for m in json.loads((BUNDLE / 'slide-map.json').read_text()) if m['counts_toward_prepared_time']) == 30
text = '\n'.join(e.get('text', '') for s in slides[6:8] for e in s['elements'])
for phrase in ['$dogpile', 'Brave web', 'arXiv', 'GitHub', 'existing projects, skills', 'Compose what fits', 'SPIA', 'DICOM', 'AnonShield + Proteus']:
    assert phrase in text, phrase
with zipfile.ZipFile(PPTX) as archive:
    pages = sorted((n for n in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)), key=lambda n: int(re.search(r'slide(\d+)', n)[1]))
    assert len(pages) == len(slides) == 32
    for i in (6, 7, 18):
        exported = ''.join(ET.fromstring(archive.read(pages[i])).itertext())
        for e in slides[i]['elements']:
            assert e['text'] in exported, e['id']
with urllib.request.urlopen('http://127.0.0.1:3016/oai-trial-current/deck.data.json', timeout=10) as response:
    payload = response.read().decode()
for sid in ids[6:8]:
    assert sid in payload, sid
assert 'Effort estimate and implementation limits' in payload
assert 'Retrospective estimate; active time was not instrumented.' in payload
for name in ['deck.public.yaml', 'WALKTHROUGH.md', 'TOC.md', 'question-map.json', 'claim_ledger.yaml']:
    current = (BUNDLE / name).read_text()
    for stale in ['recorded overrun', 'the overrun', 'post-timebox', 'elapsed work exceeded eight hours']:
        assert stale not in current, (name, stale)
handout = ROOT / 'docs/DESIGN_DECISIONS_AND_LIMITATIONS.md'
for target in re.findall(r'\]\(([^)]+)\)', handout.read_text()):
    assert (handout.parent / target.split('#')[0]).is_file(), target
print('PASS: research and reuse visible in 32-slide PPTX and live viewer payload; 30-minute prepared allocation; handout links resolve. No visual or runtime qualification implied.')
