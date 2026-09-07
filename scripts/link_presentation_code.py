"""Generate current slide/concept source ranges; never start a debuggee."""
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'docs/pitch/oai-trial/reorganized'
d=json.loads((B/('deck.document.json' if (B/'deck.document.json').exists() else 'deck.public.yaml')).read_text());old=json.loads((B/'debugger.json').read_text())['slides'];sm={m['slide_id']:m for m in json.loads((B/'slide-map.json').read_text())}
def target(path,start,end,launch=None,stop=None,locals=None):
 lines=(R/path).read_text().splitlines();assert 1<=start<=end<=len(lines),(path,start,end)
 t={'file':path,'line':start,'endLine':end,'endColumn':len(lines[end-1])+1}
 if launch:t.update(launch=launch,breakLine=stop or start,locals=locals or [])
 return t
def symbol(file,name,launch=None,stop=None,locals=None):
 path='src/anonymization_trial/'+file;nodes=ast.parse((R/path).read_text()).body
 for part in name.split('.'):
  n=next(n for n in nodes if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==part);nodes=n.body
 a=min([n.lineno]+[x.lineno for x in getattr(n,'decorator_list',[])]);return target(path,a,n.end_lineno,launch,stop,locals)
def narrative(sid):
 key=sm[sid]['narrative_sections'][0].split('#')[1];p='docs/pitch/oai-trial/reorganized/NARRATIVE.md';lines=(R/p).read_text().splitlines();start=next(i+1 for i,x in enumerate(lines) if x==f'<a id="{key}"></a>');end=next((i for i in range(start,len(lines)) if lines[i].startswith('<a id=')),len(lines));return target(p,start,max(start,end))
def flatten(elements):
 for e in elements or []:
  yield e
  yield from flatten(e.get('children'))
config={}
for s in d['slides']:
 elements=list(flatten(s['elements']))
 if s['id'] in ['r01-toc','r29-discussion','r30-thank-you']:continue
 refs=sm[s['id']]['code_refs'];base=narrative(s['id'])
 if refs and s['id'] not in ['r14-cloud','r17-disclosure','r25-lineage','r26-wrapper']:
  r=refs[0];base=target(r['path'],r['line_start'],r['line_end'])
 if s['id']=='r03-demo-observations':base=target('TRIAL_BRIEF.md',13,25)
 if s['id']=='r09-identity':base=symbol('pseudonyms.py','build_replacements','Pitch: identity',104,['replacements'])
 if s['id']=='r12-typed-locations':base=symbol('verification.py','_typed_equal','Pitch: typed',136,['a','b'])
 if s['id']=='r13-publication':base=symbol('pipeline.py','_publish','Pitch: publication',210,['report_path','output_corpus'])
 concepts={e['id']:dict(base) for e in elements if e.get('kind',e.get('type')) in ['text','asset','image','group','svg'] and e.get('role')!='decorative'}
 if s['id']=='r06-output-evidence':
  concepts['body-0']=target('scripts/qualify_submission.py',83,123)
  concepts['body-1']=target('scripts/qualify_submission.py',124,131)
  concepts['body-2']=target('scripts/qualify_submission.py',223,280)
 if s['id']=='r08-policy':
  for k in ['message','body-2']:concepts[k]=symbol('policy.py','_check_overlap')
  concepts['body-1']=symbol('policy.py','Rule.identity')
 if s['id']=='r09-identity':concepts['message']=symbol('policy.py','Rule.identity')
 if s['id']=='r10-spans':concepts['message']=symbol('matcher.py','Matcher.replace');concepts['main-visual']=symbol('matcher.py','_select')
 if s['id']=='r21-answer-verifier':
  concepts['body-0']=symbol('verification.py','_verify_locations');concepts['body-1']=target('src/anonymization_trial/verification.py',1,25)
  ref=next(r for r in refs if r.get('symbol')=='readback');concepts['body-2']=target(ref['path'],ref['line_start'],ref['line_end']);concepts['message']=concepts['body-2']
 if s['id']=='r06b-research-adoption':
  concepts['body-0']=symbol('verification.py','_verify_subject_level');concepts['body-1']=target('security/tests/test_verifier_sensitivity.py',56,91);concepts['body-2']=target('src/anonymization_trial/pseudonyms.py',30,43)
 if 'demo-command' in concepts:concepts['demo-command']=symbol('__main__.py','main')
 if s['id']=='r03-demo-observations':
  for key in concepts:
   if 'requirement' in key:concepts[key]=target('TRIAL_BRIEF.md',13,25)
   elif key.startswith('coverage-0'):concepts[key]=symbol('formats.py','transform_file')
   elif key.startswith('coverage-1'):concepts[key]=symbol('verification.py','verify_corpus')
   elif key.startswith('coverage-2'):concepts[key]=target('Dockerfile',1,len((R/'Dockerfile').read_text().splitlines()))
   elif key.startswith('coverage-3'):concepts[key]=narrative('r23-answer-scale')
 if s['id']=='r23-answer-scale':
  for key in concepts:
   if key.endswith('-hmac') or key=='local-versus-model-panel-2-row-2':
    path='docs/pitch/oai-trial/reorganized/sources/aws-key-definitions.md';concepts[key]=target(path,1,len((R/path).read_text().splitlines()))
 if s['id']=='r21-answer-verifier':
  for key in concepts:
   if key.startswith('verification-boundary-panel-3'):
    concepts[key]=target('scripts/qualify_submission.py',80,134)
   elif key.startswith('verification-boundary-panel-2'):concepts[key]=symbol('verification.py','verify_corpus')
 if 'source-navigation' in concepts and refs:
  r=refs[0];concepts['source-navigation']=target(r['path'],r['line_start'],r['line_end'])
 if s['id'] in ['r06a-research-reuse','r06b-research-adoption'] and 'source-navigation' in concepts:
  p='docs/pitch/oai-trial/reorganized/sources/research-workflow.md';concepts['source-navigation']=target(p,1,len((R/p).read_text().splitlines()))
 # Limitations jump to explanatory evidence rather than pretend missing production code exists.
 if 'qualifier' in concepts:concepts['qualifier']=narrative(s['id'])
 valid_ids={e['id'] for e in elements}
 base['concepts']={k:v for k,v in concepts.items() if k in valid_ids};config[s['id']]=base
(B/'debugger.json').write_text(json.dumps({'schema':'pitchdeck.debugger_map.v1','slides':config},indent=2)+'\n')
print(len(config),'slide mappings;',sum(len(s['concepts']) for s in config.values()),'concept mappings')
