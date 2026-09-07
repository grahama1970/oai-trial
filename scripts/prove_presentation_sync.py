"""Exercise concept selection through the live deck UI; read back VS Code receipts.

No debuggee starts here. This requires an existing trusted VS Code workspace,
Surf, and the dedicated local presentation server. It changes only UI selection.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
SURF = Path.home() / 'workspace/experiments/agent-skills/skills/surf/run.sh'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--tab-id', default=os.environ.get('PITCHDECK_SYNC_TAB'))
p.add_argument('--negative-only', action='store_true')
p.add_argument('--output', type=Path, required=True)
p.add_argument('--all', action='store_true', help='Exercise every unique mapped range')
p.add_argument('--slide', action='append', help='Limit an interrupted sweep to named slides')
a = p.parse_args()
if not a.tab_id:
    tabs = json.loads(subprocess.check_output([str(SURF), 'tab.list', '--json'], text=True))
    candidates = [t for t in tabs if t.get('url', '').startswith('http://127.0.0.1:3016/')]
    if len(candidates) != 1:
        p.error('provide --tab-id when the live OAI deck is missing or ambiguous')
    a.tab_id = str(candidates[0]['id'])
config = json.loads((ROOT / 'docs/pitch/oai-trial/reorganized/debugger.json').read_text())['slides']
cases = []
seen = set()
for slide, mapping in config.items():
    if a.slide and slide not in a.slide: continue
    for concept, target in mapping['concepts'].items():
        key = (target['file'], target['line'], target['endLine'], target['endColumn'])
        if key not in seen and (a.all or (slide, concept) in [('r09-identity','message'),('r12-typed-locations','title'),('r13-publication','title'),('r08-policy','body-2'),('r21-answer-verifier','message')]):
            seen.add(key); cases.append((slide, concept, target))
results = []
for slide, concept, target in ([] if a.negative_only else cases):
    # Browser input drives the existing React handlers; only status reads use GET.
    script = '''(async()=>{
      const slide=SLIDE, concept=CONCEPT, expected=EXPECTED;
      const wait=ms=>new Promise(r=>setTimeout(r,ms));
      location.hash='/slide/'+slide;
      for(let i=0;i<60;i++){
        const option=document.querySelector('[data-qid="deck:debug:concept"] option[value="'+concept+'"]');
        const sync=document.querySelector('[data-qid="deck:debug:sync"]');
        if(sync?.getAttribute('aria-pressed')==='false')sync.click();
        if(option && document.querySelector('[data-qid="deck:slide:'+slide+'"]'))break;
        await wait(100);
      }
      const select=document.querySelector('[data-qid="deck:debug:concept"]');
      if(!select)throw Error('concept selector unavailable');
      select.value=concept;select.dispatchEvent(new Event('change',{bubbles:true}));
      for(let i=0;i<120;i++){
        if(location.hash!=='#/slide/'+slide)throw Error('navigation changed outside this probe');
        const response=await fetch('/api/debugger?slide='+encodeURIComponent(slide)+'&concept='+encodeURIComponent(concept));
        const state=await response.json(), reveal=state.receipt?.reveal;
        if(!state.busy && reveal?.file.endsWith('/'+expected.file) && reveal.line===expected.line && reveal.endLine===expected.endLine && reveal.endColumn===expected.endColumn && reveal.selected)return JSON.stringify(state);
        await wait(100);
      }
      throw Error('VS Code selection did not settle');
    })()'''.replace('SLIDE',json.dumps(slide)).replace('CONCEPT',json.dumps(concept)).replace('EXPECTED',json.dumps(target))
    proc = subprocess.run([str(SURF),'js',script,'--tab-id',a.tab_id,'--no-activate','--no-screenshot'],text=True,capture_output=True,timeout=35)
    if proc.returncode: raise RuntimeError(proc.stderr or proc.stdout)
    state = json.loads(proc.stdout)
    if isinstance(state,str): state=json.loads(state)
    path = Path(state['receipt']['artifactLocations']['statusPath'])
    receipt = json.loads(path.read_text())
    assert receipt['id']==state['receipt']['id'] and receipt['proofValid']
    reveal=receipt['reveal']
    assert reveal['selected'] and (reveal['endLine'],reveal['endColumn'])>(reveal['line'],reveal['column'])
    assert not receipt.get('sessionState'), 'reveal unexpectedly created a debug session'
    results.append({'slide':slide,'concept':concept,'target':target,'receipt':str(path),'observed':reveal})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({'scope':'live UI reveal only; no debug execution','results':results},indent=2))
    print(slide,concept,'SELECTED',flush=True)
# Invalid concept must be refused before touching the VS Code bridge request.
request_path=ROOT/'.vscode/debugger-bridge/request.json'
before=request_path.read_bytes()
request=urllib.request.Request('http://127.0.0.1:3016/api/debugger',method='POST',data=json.dumps({'action':'reveal','slide_id':'r09-identity','concept_id':'not-an-element'}).encode(),headers={'Content-Type':'application/json','X-Pitchdeck-Control':'1','X-Pitchdeck-Deck':'/oai-trial-current/deck.data.json'})
try:
    urllib.request.urlopen(request,timeout=10)
    raise AssertionError('invalid concept accepted')
except urllib.error.HTTPError as error:
    assert error.code==409
assert request_path.read_bytes()==before
print('SYNC_READBACK_PASS; invalid concept refused; no debuggee started')
