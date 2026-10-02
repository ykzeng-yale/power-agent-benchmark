#!/usr/bin/env python3
"""Exposed engineering sensitivity only; frozen primary results never changed.

Each variant loads the exact locked scorer into a fresh in-memory namespace.
Only one explicitly recorded contract condition is changed per isolated variant.
The combined diagnostic applies four. No scientific oracle threshold changes.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, importlib.util, inspect, json, sys

ROOT=Path('/Users/yukangzengcmac/Power-Agent')
REPO=ROOT/'power-agent-benchmark'
COHORT=REPO/'cohorts/workflow-capabilities-20261002'
RUN=REPO/'results/haiku-linux-workflow-capabilities-20261002'
OUT=ROOT/'jsm-2026/multi-agent-20261002'
VERSION='workflow-capabilities-posthoc-contract2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def fresh_scorer(changes,scorer_path=None):
    spec=importlib.util.spec_from_file_location('isolated_contract_scorer',scorer_path or COHORT/'runner/score.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    patches=[]
    bodies={name:inspect.getsource(getattr(module,name))for name in['check_sources','check_execution','check_artifacts']}
    def amend(function_name,old,new):
        body=bodies[function_name]
        if body.count(old)!=1:raise RuntimeError('Frozen function target changed: '+function_name)
        bodies[function_name]=body.replace(old,new)
        patches.append({'function':function_name,'old':old,'new':new})
    if 'search_chain'in changes:
        # Still require a real successful provider search with matching trace,
        # before the named-document read; the read/hash/date/scope/citation
        # gates remain in the original function. An empty search result is an
        # attempted successful provider search, not discovery of the document.
        amend('check_sources',
          "search_positions=[i for i,t in searches if any(isinstance(other,dict) and other.get('id')in array(t.get('source_ids')) and equivalent_source(other.get('url',''),oracle['source_url']) and isinstance(other.get('content'),str) and other['content'].strip() and digest(other['content'].encode())==other.get('content_sha256') for other in sources)]",
          "search_positions=[i for i,t in searches if obj(t.get('results')).get('provider') and any(isinstance(r,dict) and r.get('tool')=='search_sources' and r.get('success')is True and r.get('query')==t.get('query') and r.get('provider')==obj(t.get('results')).get('provider') for r in array(record.get('source_requests')))]")
    if 'review_IDs'in changes:
        body=bodies['check_execution']
        old="verification=[e for e in array(record.get('executions')) if successful_execution(e) and e.get('role')in ['reviewer','self_reviewer'] and e.get('id')in ids]"
        new="verification=[e for e in array(record.get('executions')) if successful_execution(e,False) and e.get('role')in ['reviewer','self_reviewer'] and e.get('id')in ids]\n if not any(successful_execution(e) and array(obj(e.get('computed')).get('results')) for e in verification):errors.append('missing_current_executed_numerical_review')"
        if body.count(old)!=1:raise RuntimeError('Frozen review target changed')
        bodies['check_execution']=body.replace(old,new);patches.append({'function':'check_execution','old':old,'new':new})
    if 'figure_basename'in changes:
        amend('check_artifacts',"f['name']in ['sensitivity.png','sensitivity.pdf'] and ","")
    if 'grounding_precision'in changes:
        # Match actual runtime grounding tolerance, exact metric/unit strings.
        # Scientific reference answers and their frozen tolerances stay fixed.
        amend('check_execution',
          "all(v.get(k)==row.get(k) for k in ['metric','value','unit'])",
          "all(v.get(k)==row.get(k) for k in ['metric','unit']) and finite(v.get('value')) and finite(row.get('value')) and abs(v['value']-row['value'])<=1e-9*max(1,abs(v['value']))")
    for name in{p['function']for p in patches}:exec(bodies[name],module.__dict__)
    return module,patches

def main():
    global REPO,COHORT,RUN,OUT
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=REPO,help='Benchmark repository containing the exact frozen cohort evaluator')
    ap.add_argument('--run',type=Path,default=RUN,help='Verified original run directory with frozen scored-results.json')
    ap.add_argument('--out',type=Path,default=OUT,help='Fresh derived-output directory; existing outputs are never overwritten')
    args=ap.parse_args();REPO=args.repo.resolve();COHORT=REPO/'cohorts/workflow-capabilities-20261002';RUN=args.run.resolve();OUT=args.out.resolve()
    output_names=['posthoc-contract-prespec.json','posthoc-contract-sensitivity.json','posthoc-contract-sensitivity.md','posthoc-output-sha256.json']
    if any((OUT/name).exists()for name in output_names):raise RuntimeError('Refuse overwrite or resume: preserve prior derived outputs and select a fresh --out directory')
    sys.path.insert(0,str(COHORT/'runner'))
    import analyze as frozen_analyze
    protocol=load(RUN/'protocol.json');scored=load(RUN/'scored-results.json');payload=load(RUN/'public-questions.json')
    for relative,digest in protocol['frozen_evaluator_files'].items():
        if sha(COHORT/relative)!=digest:raise RuntimeError('Frozen evaluator changed:'+relative)
    expected={j['job_id']for j in protocol['jobs']}
    if len(scored['records'])!=64 or {r['job_id']for r in scored['records']}!=expected:raise RuntimeError('Incomplete planned accounting')
    oracle={o['id']:o for o in load(COHORT/'audited/oracles.json')['tasks']}
    question={t['id']:t['query']for t in payload['tasks']}
    variants={'frozen_original':[], 'search_chain_only':['search_chain'], 'review_IDs_only':['review_IDs'], 'figure_basename_only':['figure_basename'], 'grounding_precision_only':['grounding_precision'], 'combined_four':['search_chain','review_IDs','figure_basename','grounding_precision']}
    OUT.mkdir(parents=True,exist_ok=True)
    prespec={'version':VERSION,'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Post hoc engineering sensitivity specified after original outcome inspection; this timestamp is before this version executes its transformations, not preregistration.','script_sha256_before_execution':sha(Path(__file__)),'frozen_protocol_sha256':sha(RUN/'protocol.json'),'frozen_scored_results_sha256':sha(RUN/'scored-results.json'),'frozen_oracle_sha256':sha(COHORT/'audited/oracles.json'),'planned_attempts':64,'variants':variants,'fixed_constraints':'No scientific oracle/tolerance/unit/design/completion/budget/current-producer/citation/companion-CSV criteria changed; no model calls or automatic missing claims supplied.'}
    (OUT/'posthoc-contract-prespec.json').write_text(json.dumps(prespec,indent=2,allow_nan=False)+'\n')
    answers={};patches={};invariants=[];changed=[]
    for name,changes in variants.items():
        scorer,patch=fresh_scorer(changes);patches[name]=patch;rows=[]
        for original in scored['records']:
            request=dict(payload['common'],**payload['profiles'][original['profile']],query=question[original['task_id']],workflowMode=original['mode'])
            result=frozen_analyze.apply_operational_contract(scorer.score(original['record'],oracle[original['task_id']]),original,original['record'],request)
            locked=original['evaluation']
            for field in['numeric_pass','design_pass','completed','completed_numeric_pass','clarification_pass','budget_contract_pass']:
                invariants.append({'variant':name,'job_id':original['job_id'],'field':field,'unchanged':result.get(field)==locked.get(field)})
            if name=='frozen_original'and result!=locked:raise RuntimeError('Cannot reproduce locked baseline')
            rows.append({k:original[k]for k in['job_id','task_id','mode','profile','repeat']}|{'outcome_kind':result['outcome_kind'],'passed':result['passed'],'source_pass':result.get('source_pass'),'evidence_pass':result.get('evidence_pass'),'artifact_pass':result.get('artifact_pass'),'reasons':result['reasons']})
            if result['passed']!=locked['passed']:changed.append({'variant':name,'job_id':original['job_id'],'frozen_passed':locked['passed'],'diagnostic_passed':result['passed']})
        cells={}
        for mode in['single','multi']:
            for profile in['shared','expanded']:
                rs=[r for r in rows if r['mode']==mode and r['profile']==profile];calc=[r for r in rs if r['outcome_kind']=='calculation'];clar=[r for r in rs if r['outcome_kind']=='clarification']
                cells[mode+'_'+profile]={'planned':16,'all_pass':sum(r['passed']for r in rs),'calculation_planned':12,'calculation_pass':sum(r['passed']for r in calc),'clarification_planned':4,'clarification_pass':sum(r['passed']for r in clar),'source_pass_calculations':sum(r['source_pass']is True for r in calc),'evidence_pass_calculations':sum(r['evidence_pass']is True for r in calc),'artifact_pass_calculations':sum(r['artifact_pass']is True for r in calc)}
        answers[name]={'conditions':cells,'rows':rows}
    invariant_ok=all(i['unchanged']for i in invariants)
    if not invariant_ok:raise RuntimeError('Scientific/operational criterion changed')
    source_hash_before=protocol['frozen_evaluator_files']['runner/score.py']
    if sha(COHORT/'runner/score.py')!=source_hash_before:raise RuntimeError('Locked scorer modified')
    output={'version':VERSION,'analyzed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'label':'Post hoc developer-exposed engineering contract sensitivity. Not preregistered validation, not a replacement accuracy estimate, not new model trials.','script_sha256':sha(Path(__file__)),'prespec_sha256':sha(OUT/'posthoc-contract-prespec.json'),'frozen_protocol_sha256':sha(RUN/'protocol.json'),'frozen_scored_results_sha256':sha(RUN/'scored-results.json'),'frozen_oracle_sha256':sha(COHORT/'audited/oracles.json'),'frozen_scorer_sha256':source_hash_before,'planned_attempts':64,'scientific_and_budget_invariant_checks':len(invariants),'all_invariants_unchanged':invariant_ok,'patches_in_fresh_in_memory_namespaces':patches,'variants':answers,'changed_pass_indicators':changed,'qualifications':['Every original primary score, original raw object and frozen evaluator file remains unchanged.','Read/hash/date/provider-scope and actual citation requirements remain; citations or artifact claims are never supplied by this script.','The search-chain sensitivity requires an actual successful provider search receipt and matching trace before the named-document read. Empty search results count as an attempted search, not discovery of the document.','Successful actual current reviewer IDs and at least one current structured numerical check are still required; stale/failed/wrong-role references are rejected.','Figure basename relaxation preserves snapshot equality, bytes/size/hash, MIME/parser, actual cited current producer and the locked companion CSV grid. It does not certify visible plot-data agreement or scientific readability.','Grounding precision only matches existing runtime numeric serialization tolerance; exact metric/unit strings and independent scientific oracle tolerances remain unchanged.','Clarification cases retain the identical missing-input criteria and all 64 planned denominator.','Numerical agreement is unchanged under every variant. These diagnostic passes do not validate the scientific assumptions, source-support claims or the model population.']}
    (OUT/'posthoc-contract-sensitivity.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    lines=['# Post hoc contract sensitivity','',output['label'],'','All four isolated variants and their combined diagnostic keep numerical/design/unit/oracle, completed status, current executed coder evidence, operational budget and clarification criteria unchanged. They use the same64retained responses; no provider calls or extra model attempts.','', '| Diagnostic | Single shared calculation | Multi shared calculation | Single expanded calculation | Multi expanded calculation |','|---|---:|---:|---:|---:|']
    for name,answer in answers.items():lines.append('|'+name+'|'+'|'.join(str(answer['conditions'][cell]['calculation_pass'])+'/12'for cell in['single_shared','multi_shared','single_expanded','multi_expanded'])+'|')
    lines+=['','All conditions retain4/4appropriate clarification outcomes, separately from calculations. The original frozen calculation strict scores remain0/12in all four cells.','']+['- '+s for s in output['qualifications']]+['',f"{len(invariants)} invariant checks passed; the scientific numeric/design/completion/clarification and budget outcomes were unchanged. The exact isolated code substitutions and changed response IDs are recorded in the JSON. Original raw/scored files and all frozen19evaluator hashes remain intact.",'']
    text='\n'.join(lines)
    for a,b in [('same64retained','same 64 retained'),('retain4/4appropriate','retain 4/4 appropriate'),('remain0/12in','remain 0/12 in'),('all64planned','all 64 planned'),('frozen19evaluator','frozen 19 evaluator')]:text=text.replace(a,b)
    (OUT/'posthoc-contract-sensitivity.md').write_text(text)
    manifest={name:sha(OUT/name)for name in output_names[:-1]}
    (OUT/'posthoc-output-sha256.json').write_text(json.dumps({'version':VERSION,'script_sha256':sha(Path(__file__)),'outputs':manifest},indent=2)+'\n')
    print(json.dumps({'invariants_unchanged':invariant_ok,'invariant_checks':len(invariants),'calculation_pass_counts':{n:{c:v['calculation_pass']for c,v in a['conditions'].items()}for n,a in answers.items()}},indent=2))

if __name__=='__main__':main()
