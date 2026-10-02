#!/usr/bin/env python3
"""Freeze a new question-only capability cohort; no model/provider calls."""
import argparse,datetime,hashlib,json,pathlib,random
ROOT=pathlib.Path(__file__).resolve().parents[1]
CORE=['scientific-harness-cli.js','scientific-harness.js','scientific-r-executor.js','scientific-reference-guard.js','scientific-r-worker.py','model-config.js','scientific-sources.js']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--runtime-dir',type=pathlib.Path,required=True);ap.add_argument('--runtime-image',required=True);ap.add_argument('--repeats',type=int,default=2);ap.add_argument('--seed',type=int,default=20261002);ap.add_argument('--forecast-limit-usd',type=float,default=35);a=ap.parse_args()
 if a.repeats!=2:ap.error('This version prespecifies two repeats; revise proposal prospectively to change it, not after outcomes.')
 if '@sha256:'not in a.runtime_image:ap.error('Supply an immutable runtime base-image digest, not a mutable tag')
 if a.out.exists():raise RuntimeError('Refuse overwrite: choose a new cohort output directory')
 sources={p:sha(a.runtime_dir/p) for p in CORE}
 validation=json.loads((ROOT/'validation/independent-verification.json').read_text())
 if validation.get('all_checks_pass')is not True:raise RuntimeError('Independent oracle verification has not passed')
 tasks=json.loads((ROOT/'audited/tasks.json').read_text());profiles=json.loads((ROOT/'audited/profiles.json').read_text())
 payload={'suite_version':tasks['suite_version'],'common':profiles['common'],'profiles':profiles['profiles'],'tasks':[{'id':t['id'],'query':t['question']}for t in tasks['tasks']]}
 jobs=[{'task_id':t['id'],'mode':m,'profile':p,'repeat':r,'job_id':f"{t['id']}__{m}__{p}__r{r}"}for t in tasks['tasks']for m in ['single','multi']for p in ['shared','expanded']for r in range(1,a.repeats+1)]
 random.Random(a.seed).shuffle(jobs)
 paths=[p for p in ROOT.rglob('*')if p.is_file() and p.suffix in ['.py','.R','.json','.md'] and '__pycache__'not in p.parts]
 frozen={str(p.relative_to(ROOT)):sha(p)for p in sorted(paths)}
 a.out.mkdir(parents=True);dump(a.out/'public-questions.json',payload)
 protocol={'protocol_version':'workflow-capabilities-protocol1','frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'suite_version':tasks['suite_version'],'runtime_image':a.runtime_image,'runtime_files':sources,'frozen_evaluator_files':frozen,'question_payload_sha256':sha(a.out/'public-questions.json'),'planned_attempts':len(jobs),'repeats':2,'seed':a.seed,'modes':['single','multi'],'profiles':profiles,'task_ids':[t['id']for t in tasks['tasks']],'jobs':jobs,'workers':3,'forecast_dispatch_limit_usd':a.forecast_limit_usd,'forecast_note':'Predictive guard limits further dispatch; it is not a bound on final billed cost. Model tokens are estimated at uncached Haiku input1/output5 USD per million; separate cache usage and provider search/read credits retained. Existing in-flight jobs finish. Undispatched jobs remain explicit planned stubs. No selected replacement or repeat-count adaptation.','primary':'All planned attempts: six calculation tasks require completed+numeric/schema/units/design+current successful R+required actual verification+actual source search and bounded document reading+citation link+delivered correct CSV+hash-verified parseable PNG/PDF. Two missing-input cases require focused material-input clarification and no unwarranted participant/cluster count. Figure scientific content has a separate predefined blinded visual rubric; file parsing alone does not certify it.','analysis':'Paired exploratory task/family descriptive contrasts for same-operation ceilings. Same-model/context-topology comparison includes blind precheck in multi versus shared self-review in single. No holdout, equal-dollar, clinical validation, random-capability-population or guaranteed multi superiority claim.','oracle_validation_sha256':sha(ROOT/'validation/independent-verification.json')}
 dump(a.out/'protocol.json',protocol)
 print(json.dumps({'protocol_sha256':sha(a.out/'protocol.json'),'question_payload_sha256':protocol['question_payload_sha256'],'planned_attempts':len(jobs),'runtime_file_count':len(sources)},indent=2))
if __name__=='__main__':main()
