#!/usr/bin/env python3
"""Frozen, judge-free primary evaluation of a command or HTTP scientific harness."""
import argparse,concurrent.futures,hashlib,json,math,pathlib,random,subprocess,tempfile,time,urllib.request,datetime,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
def canonical(value):return str(value).lower().strip().replace('-','_').replace(' ','_')
ALIASES={
 'method':{'two_sample_t_test':'two_sample_t','pooled_two_sample_t_test':'two_sample_t','paired_t_test':'paired_t','one_sample_t_test':'one_sample_t','one_way_anova_omnibus':'one_way_anova','repeated_measures_anova_between_factors':'rm_between','repeated_measures_anova_within_factors':'rm_within','pmsampsize_binary':'riley_binary','pmsampsize_survival':'riley_survival'},
 'alternative':{'one_tailed':'one_sided','two_tailed':'two_sided','omnibus':'not_applicable'},
 'unit':{'subjects_per_group':'participants_per_group','subjects_total':'participants_total','total_participants':'participants_total','per_group':'participants_per_group','per_cell':'participants_per_cell','total':'participants_total'}
}
def norm(x,field):v=canonical(x);return ALIASES.get(field,{}).get(v,v)
def _frozen_score(record,oracle):
 errors=[];numeric=False;unit=False;design=True;schema=True;evidence=False
 if not isinstance(record,dict):return {'passed':False,'reason':['invalid_record'],'numeric_pass':False,'unit_pass':False,'design_pass':False,'evidence_pass':False,'schema_pass':False}
 if record.get('evaluation_version_changed'):errors.append('frozen_version_changed')
 if record.get('scientificStatus',record.get('status'))!='completed' or record.get('success') is not True:errors.append('not_completed')
 results=record.get('results',record.get('answer',{}).get('results',[]))
 if not isinstance(results,list):results=[];schema=False
 candidates=[x for x in results if isinstance(x,dict) and norm(x.get('metric'),'metric')==oracle['metric']]
 if len(candidates)!=1:schema=False;errors.append('missing_or_ambiguous_primary_metric')
 else:
  c=candidates[0];v=c.get('value');schema=type(v)in(int,float) and math.isfinite(v)
  if schema:
   numeric=abs(v-oracle['value'])<=oracle['absolute_tolerance']+1e-12
   if oracle['metric']=='sample_size' and (v<1 or v!=int(v)):numeric=False
  else:errors.append('invalid_numeric_schema')
  unit=norm(c.get('unit'),'unit')==norm(oracle['unit'],'unit')
  if not numeric:errors.append('numeric_mismatch')
  if not unit:errors.append('unit_mismatch')
 d=record.get('design') or {};expected=oracle['design']
 for key,want in expected.items():
  if want is None:continue
  got=d.get(key)
  ok=(type(got)in(int,float) and abs(got-want)<1e-12) if type(want)in(int,float) else norm(got,key)==norm(want,key)
  if not ok:design=False;errors.append('design_'+key+'_mismatch')
 executions=record.get('executions',[])
 evidence=any(x.get('success') is True and x.get('role')=='coder' and x.get('exitCode') in [0,None] and x.get('computed') and x.get('code_sha256')==hashlib.sha256(x.get('code','').encode()).hexdigest() for x in executions if isinstance(x,dict))
 if not evidence:errors.append('missing_execution_evidence')
 # Verify the final primary claim also occurs in computed R evidence, even for other providers.
 if candidates and evidence:
  c=candidates[0];linked=any(y.get('metric')==c.get('metric') and y.get('value')==c.get('value') and y.get('unit')==c.get('unit') for x in executions if x.get('success') for y in (x.get('computed') or {}).get('results',[]))
  if not linked:evidence=False;errors.append('result_not_in_execution_evidence')
 return {'passed':not errors and schema and numeric and unit and design and evidence,'reason':errors,'numeric_pass':numeric,'unit_pass':unit,'design_pass':design,'evidence_pass':bool(evidence),'schema_pass':bool(schema),'agent_value':candidates[0].get('value') if len(candidates)==1 else None,'expected_value':oracle['value']}
def schema_failure(error):
 return {'passed':False,'reason':['invalid_provider_schema'],'numeric_pass':False,'unit_pass':False,'design_pass':False,'evidence_pass':False,'schema_pass':False,'scorer_error_type':type(error).__name__}
def score(record,oracle):
 # The canonical top-level results remain valid independently of optional answer.
 # Null/malformed fallback fields cannot crash the evaluation pipeline.
 if isinstance(record,dict):
  record=dict(record)
  if not isinstance(record.get('answer'),dict):record['answer']={}
 try:return _frozen_score(record,oracle)
 except Exception as error:return schema_failure(error)
def persist_and_score(file,job,record,duration,oracle,scorer=None):
 # Persist the unchanged provider record BEFORE any scorer invocation.
 out=dict(job,record=record,duration_seconds=duration,evaluation_pending=True)
 file.write_text(json.dumps(out,indent=2)+'\n')
 try:evaluation=(scorer or score)(record,oracle)
 except Exception as error:evaluation=schema_failure(error)
 out.pop('evaluation_pending',None);out['evaluation']=evaluation
 temporary=file.with_suffix('.partial');temporary.write_text(json.dumps(out,indent=2)+'\n');temporary.replace(file)
 return out
def public_request(task,mode):
 # Only answer-free question and output conventions reach the agent. Never task ID/source/oracle.
 method=next(s['method'] for s in json.loads((ROOT/'audited/reference-specifications.json').read_text()) if s['id']==task['id'])
 contract=task['response_contract']
 query=task['question']+f"\nFor structured reporting use primary metric '{contract['metric']}' and unit '{contract['unit']}'. Use study-design method identifier '{method}'. Keep all numerical values grounded in executed code."
 return {'query':query,'workflowMode':mode,'maxModelCalls':18,'maxExecutions':8,'maxRepairs':1,'deadlineMs':300000}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def source_hashes(extra=None):
 paths=['audited/tasks.json','audited/oracles.json','audited/reference-specifications.json','runner/audited_benchmark.py','runner/audited_benchmark_v2_0_1.py','runner/audited_benchmark_v2_0_2.py','runner/audited_benchmark_v2_0_3.py','validation/reference.R','validation/independent.py']
 if (ROOT/'validation/runtime-baseline.json').exists():paths.append('validation/runtime-baseline.json')
 output={p:sha(ROOT/p) for p in paths}
 if extra:
  for p in [extra,extra.with_name('scientific-harness.js'),extra.with_name('scientific-r-executor.js'),extra.with_name('model-config.js'),extra.with_name('scientific-r-worker.py')]:
   if p.exists():output[str(p)]=sha(p)
  # Explicit absence supports archived guardless releases and detects later
  # addition/removal as well as byte changes without altering old manifests.
  guard=extra.with_name('scientific-reference-guard.js')
  output[str(guard)]=sha(guard) if guard.exists() else None
 return output
def wilson(k,n,z=1.959963984540054):
 if not n:return [None,None]
 p=k/n;den=1+z*z/n;mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return [mid-half,mid+half]
def summarize(records,tasks):
 output={};task_by={t['id']:t for t in tasks}
 for mode in sorted(set(x['mode'] for x in records)):
  rs=[x for x in records if x['mode']==mode];n=len(rs);k=sum(x['evaluation']['passed'] for x in rs)
  rates={id:sum(x['evaluation']['passed'] for x in rs if x['task_id']==id)/sum(x['task_id']==id for x in rs) for id in sorted(set(x['task_id'] for x in rs))}
  output[mode]={'planned_attempts':n,'passed':k,'pass_rate':k/n if n else None,'descriptive_wilson_95':wilson(k,n),'complete':sum(x['record'].get('success') is True for x in rs),'per_task_pass_rate':rates,'median_seconds':statistics.median(x['duration_seconds'] for x in rs) if n else None,'usage':{key:sum(x['record'].get('usage',{}).get(key,0) for x in rs) for key in ['input_tokens','output_tokens']},'tiers':{str(tier):{'attempts':sum(task_by[x['task_id']]['tier']==tier for x in rs),'passed':sum(x['evaluation']['passed'] for x in rs if task_by[x['task_id']]['tier']==tier)} for tier in range(1,5)}}
 if 'single'in output and 'multi'in output:
  keys=set(output['single']['per_task_pass_rate'])&set(output['multi']['per_task_pass_rate']);d=[output['multi']['per_task_pass_rate'][k]-output['single']['per_task_pass_rate'][k] for k in sorted(keys)]
  family_differences={}
  for id,diff in zip(sorted(keys),d):family_differences.setdefault(task_by[id].get('family',id),[]).append(diff)
  clusters=list(family_differences.values());rng=random.Random(20261001);boots=[]
  for _ in range(10000):
   sampled=[rng.choice(clusters)for _ in clusters];flat=[v for cluster in sampled for v in cluster]
   if flat:boots.append(sum(flat)/len(flat))
  boots.sort()
  output['paired_comparison']={'task_count':len(d),'source_family_count':len(clusters),'mean_task_pass_rate_difference_multi_minus_single':sum(d)/len(d) if d else None,'source_family_cluster_bootstrap_95':[boots[249],boots[9749]] if boots else None,'note':'Bootstrap resamples source families, keeping related tasks/repeats/modes together. Public developer-exposed exploratory suite; not a random sample of scientific capability. Wilson intervals are descriptive and ignore within-family dependence.'}
 return output
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cli',type=pathlib.Path);ap.add_argument('--endpoint');ap.add_argument('--node',default='node');ap.add_argument('--repeats',type=int,default=3);ap.add_argument('--modes',nargs='+',default=['single','multi']);ap.add_argument('--split',choices=['pilot','development','evaluation','all'],default='pilot');ap.add_argument('--workers',type=int,default=3);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--freeze-only',action='store_true');a=ap.parse_args()
 if a.repeats<1 or a.workers<1:ap.error('repeats and workers must be positive')
 if not a.cli and not a.endpoint and not a.freeze_only:ap.error('provide --cli or --endpoint')
 manifest=json.loads((ROOT/'audited/tasks.json').read_text());tasks=[t for t in manifest['tasks'] if a.split=='all' or (a.split=='pilot' and t['pilot']) or t['split']==a.split];oracles={o['id']:o for o in json.loads((ROOT/'audited/oracles.json').read_text())['tasks']}
 jobs=[{'task_id':t['id'],'repeat':r,'mode':mode}for t in tasks for r in range(1,a.repeats+1)for mode in a.modes];random.Random(20261001).shuffle(jobs)
 a.out.mkdir(parents=True,exist_ok=True);hashes=source_hashes(a.cli);protocol={'version':'2.0.3-six-dependency-raw-first','frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task_ids':[t['id']for t in tasks],'randomization_seed':20261001,'repeats':a.repeats,'modes':a.modes,'jobs':jobs,'hashes':hashes,'budgets':{'model_calls':18,'executions':8,'repairs':1,'deadline_seconds':300},'primary':'All planned attempt strict pass: completed + schema + units + design + numerical oracle + executed evidence. No retries/LLM extraction.','inference':'Source-family cluster bootstrap and paired task-level descriptive difference. Pilot is purposive and public, not contamination-free holdout.'}
 protocol['runtime_baseline']=json.loads((ROOT/'validation/runtime-baseline.json').read_text()) if (ROOT/'validation/runtime-baseline.json').exists() else None
 protocol_path=a.out/'protocol.json'
 if protocol_path.exists():raise RuntimeError('Refusing to overwrite a frozen run; choose a fresh output directory')
 protocol_path.write_text(json.dumps(protocol,indent=2)+'\n')
 if a.freeze_only:print('Protocol frozen without model calls');return
 byid={t['id']:t for t in tasks}
 def run(j):
  if source_hashes(a.cli)!=hashes:
   file=a.out/f"{j['task_id']}__{j['mode']}__r{j['repeat']}.json"
   return persist_and_score(file,j,{'status':'version_changed','scientificStatus':'version_changed','success':False},0,oracles[j['task_id']])
  started=time.monotonic();request=public_request(byid[j['task_id']],j['mode'])
  try:
   if a.cli:
    with tempfile.TemporaryDirectory(prefix='pa26-blind-') as td:
     p=subprocess.run([a.node,str(a.cli.resolve()),'--mode',j['mode'],'--deadline-ms','300000'],input=json.dumps(request),text=True,capture_output=True,cwd=td,timeout=330)
    if p.returncode:raise RuntimeError('provider_process_error: '+p.stderr[-500:])
    record=json.loads(p.stdout)
   else:
    req=urllib.request.Request(a.endpoint,data=json.dumps(dict(request,stream=False)).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=330)as r:record=json.load(r)
   if source_hashes(a.cli)!=hashes:record['evaluation_version_changed']=True
  except Exception as e:record={'status':'provider_error','scientificStatus':'provider_error','success':False,'error':str(e)}
  file=a.out/f"{j['task_id']}__{j['mode']}__r{j['repeat']}.json";return persist_and_score(file,j,record,round(time.monotonic()-started,3),oracles[j['task_id']])
 records=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers)as pool:
  for future in concurrent.futures.as_completed([pool.submit(run,j)for j in jobs]):
   out=future.result();records.append(out);print(f"{len(records)}/{len(jobs)} {out['task_id']} {out['mode']} r{out['repeat']}: {'PASS' if out['evaluation']['passed'] else 'FAIL'} ({out['record'].get('status')})",flush=True)
 summary={'protocol_sha256':sha(protocol_path),'suite_version':manifest['suite_version'],'planned_attempts':len(jobs),'recorded_attempts':len(records),'summary':summarize(records,tasks),'records':records};(a.out/'results.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary['summary'],indent=2))
if __name__=='__main__':main()
