#!/usr/bin/env python3
"""Offline complete-denominator capability assessment. No LLM extraction."""
import argparse,base64,collections,hashlib,json,pathlib,random,statistics
from score import score
from dispatch import token_cost
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def check_budget(record,request):
 b=record.get('budget')or{};g=b.get('global')or{};u=b.get('used')or{};p=b.get('profile')or{};errors=[]
 if record.get('workflowMode')!=request['workflowMode'] or record.get('verificationPolicy')!='required':errors.append('workflow_or_verification_contract_mismatch')
 for key in ['maxModelCalls','maxExecutions','deadlineMs','maxSearches','maxSourceReads','maxSourceChars']:
  if g.get(key)!=request[key]:errors.append('global_limit_mismatch:'+key)
 for key,value in request['budgetProfile'].items():
  if p.get(key)!=value:errors.append('profile_limit_mismatch:'+key)
 for key,limit in [('model_calls',request['maxModelCalls']),('executions',request['maxExecutions']),('searches',request['maxSearches']),('source_reads',request['maxSourceReads']),('source_chars',request['maxSourceChars'])]:
  actual=u.get(key)
  if type(actual)is not int or actual<0 or actual>limit:errors.append('used_limit_invalid:'+key)
 if u.get('executions')!=len(record.get('executions')or[]):errors.append('execution_count_ledger_mismatch')
 # Per-phase caps are ceilings per invocation, always bounded by globals.
 for phase in b.get('phases')or[]:
  for used,max_ in [('model_calls','max_model_calls'),('executions','max_executions')]:
   if type(phase.get(used))is not int or type(phase.get(max_))is not int or not 0<=phase[used]<=phase[max_]:errors.append('phase_limit_invalid:'+str(phase.get('name')))
 return errors

def apply_operational_contract(evaluation,row,parsed,request):
 errors=check_budget(parsed,request)if isinstance(parsed,dict)else['invalid_provider_record']
 if row.get('runtime_changed'):errors.append('runtime_changed_during_attempt')
 if row.get('exit_code')not in [0,None]or row.get('process_error')or row.get('capture_error'):errors.append('provider_process_or_capture_error')
 evaluation['budget_contract_pass']=not errors;evaluation['reasons'].extend(errors)
 if errors:evaluation['passed']=False
 return evaluation

def provider_usage(records):
 requests=[s for r in records for s in (r.get('record',{}).get('source_requests')or[])if isinstance(s,dict)]
 observed=collections.Counter();known=unknown=0
 for request in requests:
  usage=request.get('additional_provider_usage')
  if not isinstance(usage,dict):unknown+=1;continue
  known+=1
  for k,v in usage.items():
   if type(v)in(int,float):observed[k]+=v
 return {'attempted_requests':len(requests),'successful_requests':sum(s.get('success')is True for s in requests),'cache_hits':sum(s.get('cache_hit')is True for s in requests),'requests_with_observed_additional_usage':known,'requests_with_unknown_usage':unknown,'observed_additional_provider_counters':dict(observed),'qualification':'Provider-reported counters/credits, not a dollar invoice. Local cache-hit credits count0; missing usage is unknown, not imputed0. Model-token estimate excludes source-provider dollar pricing.'}

def summarize(records,tasks):
 by={t['id']:t for t in tasks};out={}
 for profile in ['shared','expanded']:
  for mode in ['single','multi']:
   rs=[r for r in records if r['mode']==mode and r['profile']==profile];key=mode+'_'+profile
   actual=[r for r in rs if r.get('dispatched') and isinstance(r.get('record'),dict)]
   positives=[r for r in rs if by[r['task_id']]['outcome_kind']=='calculation'];negatives=[r for r in rs if by[r['task_id']]['outcome_kind']=='clarification']
   out[key]={'planned_attempts':len(rs),'dispatched_attempts':sum(r.get('dispatched')is True for r in rs),'transport_captured':sum(r.get('transport_captured')is True for r in rs),'actual_provider_records':len(actual),'undispatched':sum(r.get('dispatched')is False for r in rs),'capture_or_process_errors':sum(bool(r.get('capture_error')or r.get('process_error')or r.get('exit_code')not in [0,None])for r in rs),'strict_pass':sum(r['evaluation']['passed']for r in rs),'calculation_tasks':{'planned_attempts':len(positives),'strict_pass':sum(r['evaluation']['passed']for r in positives),'numeric_agreement':sum(r['evaluation'].get('numeric_pass')is True for r in positives),'completed_numeric_agreement':sum(r['evaluation'].get('completed_numeric_pass')is True for r in positives),'source_acquisition':sum(r['evaluation'].get('source_pass')is True for r in positives),'artifact_delivery_and_data':sum(r['evaluation'].get('artifact_pass')is True for r in positives)},'missing_input_tasks':{'planned_attempts':len(negatives),'appropriate_clarification':sum(r['evaluation'].get('clarification_pass')is True for r in negatives)},'observed_statuses':dict(collections.Counter((r['record'].get('scientificStatus')or r['record'].get('status')or'unknown')for r in actual)),'median_observed_seconds':statistics.median(r['duration_seconds']for r in actual if type(r.get('duration_seconds'))in [int,float])if any(type(r.get('duration_seconds'))in [int,float]for r in actual)else None,'usage_observed':{k:sum((r['record'].get('usage')or{}).get(k,0)or 0 for r in actual)for k in ['input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens']},'operation_usage_observed':{k:sum((r['record'].get('budget')or{}).get('used',{}).get(k,0)or 0 for r in actual)for k in ['model_calls','executions','searches','source_reads','source_chars']},'scientific_figure_content':'Requires separate frozen blinded visual rubric; parseable delivery is not content certification.'}
  for mode in ['single','multi']:
   key=mode+'_'+profile
   actual=[r for r in records if r['mode']==mode and r['profile']==profile and r.get('dispatched') and isinstance(r.get('record'),dict)]
   out[key]['uncached_token_cost_estimate_usd']=sum(token_cost(r['record'])for r in actual)
   out[key]['source_provider_usage_observed']=provider_usage(actual)
   out[key]['required_verification_coverage']={'reviewer_started':sum((r['record'].get('verification')or{}).get('reviewer_started')is True for r in actual),'accepted_review':sum((r['record'].get('verification')or{}).get('review_accepted')is True for r in actual),'successful_blind_precheck':sum((r['record'].get('verification')or{}).get('successful_precheck_executed')is True for r in actual),'requested_fresh_context':sum((r['record'].get('verification')or{}).get('requested_independent_agent_review')is True for r in actual)}
 comparisons={}
 for profile in ['shared','expanded']:
  differences={}
  for t in tasks:
   mode_rates={m:sum(r['evaluation']['passed']for r in records if r['task_id']==t['id'] and r['profile']==profile and r['mode']==m)/sum(1 for r in records if r['task_id']==t['id'] and r['profile']==profile and r['mode']==m)for m in ['single','multi']}
   differences[t['id']]=mode_rates['multi']-mode_rates['single']
  families={}
  for t in tasks:families.setdefault(t['family'],[]).append(differences[t['id']])
  clusters=list(families.values());rng=random.Random(20261002);samples=[]
  for _ in range(10000):
   picked=[rng.choice(clusters)for _ in clusters];flat=[v for c in picked for v in c];samples.append(sum(flat)/len(flat))
  samples.sort()
  comparisons[profile]={'task_paired_mean_multi_minus_single':sum(differences.values())/len(differences),'source_family_count':len(families),'source_family_cluster_bootstrap95':[samples[249],samples[9749]],'per_task_difference':differences,'interpretation':'Exploratory descriptive selected-task/family variability; two repeated calls per task/condition. Only six selected family labels, including missing-input cases; not a confidence interval for general scientific capability. Operational denominator includes all planned jobs.'}
 out['paired_modes_by_profile']=comparisons
 out['capacity_effect_by_mode']={m:{'expanded_minus_shared_strict_rate':out[m+'_expanded']['strict_pass']/out[m+'_expanded']['planned_attempts']-out[m+'_shared']['strict_pass']/out[m+'_shared']['planned_attempts'],'interpretation':'Budget-profile and wall-clock capacity contrast; actual tokens, costs and search/read usage need separate comparison, not an architecture-only causal effect.'}for m in ['single','multi']}
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path);a=ap.parse_args();out=a.out or a.run/'scored-results.json'
 if out.exists():raise RuntimeError('Preserve previous analyzed artifacts: select a new output filename')
 protocol=json.loads((a.run/'protocol.json').read_text());payload=json.loads((a.run/'public-questions.json').read_text());psha=sha(a.run/'protocol.json')
 if sha(a.run/'public-questions.json')!=protocol['question_payload_sha256']:raise RuntimeError('Question payload mismatch')
 for relative,digest in protocol['frozen_evaluator_files'].items():
  if sha(ROOT/relative)!=digest:raise RuntimeError('Frozen evaluator dependency changed:'+relative)
 tasks=json.loads((ROOT/'audited/tasks.json').read_text())['tasks'];oracle={x['id']:x for x in json.loads((ROOT/'audited/oracles.json').read_text())['tasks']};question={t['id']:t for t in payload['tasks']};records=[];missing=[]
 for job in protocol['jobs']:
  path=a.run/f"{job['job_id']}.json"
  if not path.exists():missing.append(job);continue
  row=json.loads(path.read_text())
  if any(row.get(k)!=v for k,v in job.items()) or row.get('protocol_sha256')!=psha:raise RuntimeError('Job/protocol binding mismatch:'+job['job_id'])
  if row.get('dispatched')is False:
   if row.get('record')is not None or row.get('transport_captured'):raise RuntimeError('Undispatched stub contains invented model response')
   evaluation={'scoring_version':'workflow-capabilities-score1','passed':False,'reasons':['not_dispatched'],'outcome_kind':oracle[job['task_id']]['kind']}
  else:
   transport_path=a.run/'transports'/f"{job['job_id']}.transport.json"
   if not transport_path.exists():raise RuntimeError('Dispatched job lacks persisted raw bytes:'+job['job_id'])
   transport=json.loads(transport_path.read_text())
   if row.get('transport_sha256')!=sha(transport_path)or transport.get('protocol_sha256')!=psha:raise RuntimeError('Raw capture identity mismatch')
   stdout=base64.b64decode(transport['stdout_base64'],validate=True)
   if hashlib.sha256(stdout).hexdigest()!=transport['stdout_sha256']:raise RuntimeError('Raw stdout digest mismatch')
   request=dict(payload['common'],**payload['profiles'][job['profile']],query=question[job['task_id']]['query'],workflowMode=job['mode'])
   if transport['request_sha256']!=hashlib.sha256(canon(request).encode()).hexdigest():raise RuntimeError('Request identity mismatch')
   try:
    parsed=json.loads(stdout,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite_json')))
    if not isinstance(parsed,dict):parsed=None
   except Exception:parsed=None
   if parsed!=row.get('record'):raise RuntimeError('Provider record differs from captured stdout')
   evaluation=score(row.get('record'),oracle[job['task_id']])
   evaluation=apply_operational_contract(evaluation,row,parsed,request)
  records.append(dict(row,evaluation=evaluation))
 if missing:raise RuntimeError('Missing planned accounting files; preserve actual records and generate explicit capture-loss accounting before analysis. Missing:'+str(len(missing)))
 data={'analysis_version':'workflow-capabilities-analysis1','protocol_sha256':psha,'planned_attempts':len(protocol['jobs']),'recorded_accounting_rows':len(records),'summary':summarize(records,tasks),'records':records}
 out.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
 print(json.dumps(data['summary'],indent=2))
if __name__=='__main__':main()
