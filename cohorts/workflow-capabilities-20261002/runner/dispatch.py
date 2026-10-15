#!/usr/bin/env python3
"""Question-only raw-first runner. This module cannot load scientific oracles.

Suitable for a separate Cloud Run Job image with ONLY this file, protocol and
public-questions.json added to an immutable backend runtime. Scoring is offline.
"""
import argparse,base64,concurrent.futures,datetime,hashlib,json,math,os,pathlib,subprocess,tempfile,time
VERSION='workflow-capabilities-dispatch1'
CORE=['scientific-harness-cli.js','scientific-harness.js','scientific-r-executor.js','scientific-reference-guard.js','scientific-r-worker.py','model-config.js','scientific-sources.js']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.partial');tmp.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def upload(p,prefix):
 if not prefix:return True
 # Authentication stays in the cloud SDK/metadata environment, never a CLI arg.
 r=subprocess.run(['gsutil','-q','cp',str(p),prefix.rstrip('/')+'/'+p.name],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=90)
 if r.returncode:raise RuntimeError('Artifact upload failed; original local bytes retained')
 return True

def token_cost(record):
 u=record.get('usage')if isinstance(record,dict)else{}
 if not isinstance(u,dict):u={}
 numeric=lambda k:u.get(k,0)if type(u.get(k,0))in(int,float) and math.isfinite(u.get(k,0)) and u.get(k,0)>=0 else 0
 # Prospective uncached-equivalent token estimate, not provider billing or a guaranteed upper bound.
 # Cache creation/read tokens are added with uncached input price, and kept
 # separately in output so readers can reconstruct other pricing conventions.
 return (sum(numeric(k)for k in ['input_tokens','cache_creation_input_tokens','cache_read_input_tokens'])+5*numeric('output_tokens'))/1000000

def make_request(payload,job):
 t=next(t for t in payload['tasks']if t['id']==job['task_id'])
 return dict(payload['common'],**payload['profiles'][job['profile']],query=t['query'],workflowMode=job['mode'])

def execute_job(job,request,cli,node,out,protocol_sha,prefix,expected_runtime,timeout_extra=30):
 started=time.monotonic();stdout=b'';stderr=b'';code=None;failure=None
 try:
  if {name:sha(cli.parent/name) for name in CORE}!=expected_runtime:raise RuntimeError('Frozen runtime dependency changed before dispatch')
  # A fresh cwd and question-only stdin. No benchmark task/oracle directory is
  # mounted into R's execution environment or attached to the author context.
  with tempfile.TemporaryDirectory(prefix='pa-capabilities-question-')as td:
   p=subprocess.run([node,str(cli),'--mode',job['mode'],'--deadline-ms',str(request['deadlineMs'])],input=json.dumps(request).encode(),capture_output=True,cwd=td,timeout=request['deadlineMs']/1000+timeout_extra)
  stdout=p.stdout;stderr=p.stderr;code=p.returncode
 except subprocess.TimeoutExpired as e:stdout=e.stdout or b'';stderr=e.stderr or b'';failure='provider_process_timeout'
 except Exception as e:failure=type(e).__name__
 duration=round(time.monotonic()-started,3)
 transport=dict(job,dispatched=True,captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol_sha256=protocol_sha,request_sha256=hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':')).encode()).hexdigest(),exit_code=code,runner_failure=failure,duration_seconds=duration,stdout_base64=base64.b64encode(stdout).decode(),stderr_base64=base64.b64encode(stderr).decode(),stdout_sha256=hashlib.sha256(stdout).hexdigest(),stderr_sha256=hashlib.sha256(stderr).hexdigest())
 raw=out/'transports'/f"{job['job_id']}.transport.json"
 # Crucial: bytes are durably persisted and uploaded BEFORE JSON.parse/scoring.
 dump(raw,transport);upload(raw,prefix+'/transports'if prefix else None)
 record=None;parse_error=None
 try:
  record=json.loads(stdout.decode('utf-8'),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite_json')))
  if not isinstance(record,dict):raise ValueError('not_object')
 except Exception as e:record=None;parse_error=type(e).__name__
 row=dict(job,dispatched=True,transport_captured=True,transport_sha256=sha(raw),protocol_sha256=protocol_sha,duration_seconds=duration,record=record,capture_error=parse_error,process_error=failure,exit_code=code)
 if {name:sha(cli.parent/name) for name in CORE}!=expected_runtime:row['runtime_changed']=True
 path=out/f"{job['job_id']}.json";dump(path,row);upload(path,prefix)
 return row

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--questions',type=pathlib.Path,required=True);ap.add_argument('--protocol',type=pathlib.Path,required=True);ap.add_argument('--cli',type=pathlib.Path,default=pathlib.Path('/app/scientific-harness-cli.js'));ap.add_argument('--node',default='node');ap.add_argument('--out',type=pathlib.Path,default=pathlib.Path('/study'));ap.add_argument('--gcs-prefix');a=ap.parse_args()
 a.cli=a.cli.resolve();payload=json.loads(a.questions.read_text());protocol=json.loads(a.protocol.read_text());psha=sha(a.protocol)
 if sha(a.questions)!=protocol['question_payload_sha256']:raise RuntimeError('Question payload hash mismatch')
 if {name:sha(a.cli.parent/name)for name in CORE}!=protocol['runtime_files']:raise RuntimeError('Frozen seven-file runtime fingerprint mismatch')
 if (a.out/'protocol.json').exists():raise RuntimeError('Refuse restart/overwrite: preserve a terminated cohort and choose a new prospectively frozen one')
 a.out.mkdir(parents=True,exist_ok=True);(a.out/'protocol.json').write_bytes(a.protocol.read_bytes());(a.out/'public-questions.json').write_bytes(a.questions.read_bytes())
 upload(a.out/'protocol.json',a.gcs_prefix);upload(a.out/'public-questions.json',a.gcs_prefix)
 jobs=list(protocol['jobs']);records=[];workers=protocol['workers'];limit=protocol['forecast_dispatch_limit_usd'];spent=0;dispatched=0;stop=False
 # Bound concurrency AND forecast using completed cost plus outstanding slots.
 # Every queued job is decided in frozen order. No outcome-based scheduling.
 # $0.20/job initial forecast; later use max($0.20,mean completed token cost).
 pending={};iterator=iter(jobs)
 with concurrent.futures.ThreadPoolExecutor(max_workers=workers)as pool:
  while True:
   while not stop and len(pending)<workers:
    mean=max(.20,spent/max(1,len(records)));forecast=spent+(len(pending)+1)*mean
    if forecast>limit:stop=True;break
    try:job=next(iterator)
    except StopIteration:break
    req=make_request(payload,job);f=pool.submit(execute_job,job,req,a.cli,a.node,a.out,psha,a.gcs_prefix,protocol['runtime_files']);pending[f]=job;dispatched+=1
   if not pending:break
   done,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
   for future in done:
    job=pending.pop(future)
    try:row=future.result()
    except Exception as e:
     # This is an operational capture/upload failure, not a made-up model status.
     raw=a.out/'transports'/f"{job['job_id']}.transport.json"
     row=dict(job,dispatched=True,transport_captured=raw.exists(),transport_sha256=sha(raw)if raw.exists()else None,protocol_sha256=psha,record=None,capture_error=type(e).__name__,model_status_unknown=True)
     path=a.out/f"{job['job_id']}.json";dump(path,row)
     try:upload(path,a.gcs_prefix)
     except Exception:pass
    records.append(row);spent+=token_cost(row.get('record')or{})
    dump(a.out/'progress.json',{'runner_version':VERSION,'completed_transport_jobs':sum(x.get('transport_captured')is True for x in records),'completed_dispatch_jobs':len(records),'dispatched':dispatched,'planned':len(jobs),'in_flight':len(pending),'uncached_token_cost_estimate_usd':spent,'forecast_limit_usd':limit,'forecast_stopped':stop})
    try:upload(a.out/'progress.json',a.gcs_prefix)
    except Exception:pass
    print(json.dumps({'completed':len(records),'planned':len(jobs),'in_flight':len(pending),'forecast_stopped':stop,'uncached_token_cost_estimate_usd':round(spent,6)}),flush=True)
 seen={r['job_id']for r in records}
 for job in jobs:
  if job['job_id']not in seen:
   row=dict(job,dispatched=False,transport_captured=False,record=None,duration_seconds=None,protocol_sha256=psha,operational_status='budget_not_started'if stop else 'runner_not_started')
   records.append(row);path=a.out/f"{job['job_id']}.json";dump(path,row);upload(path,a.gcs_prefix)
 aggregate={'runner_version':VERSION,'protocol_sha256':psha,'planned_attempts':len(jobs),'dispatched_attempts':dispatched,'transport_captured_attempts':sum(r.get('transport_captured')is True for r in records),'undispatched_attempts':sum(r.get('dispatched')is False for r in records),'uncached_token_cost_estimate_usd':spent,'records':records}
 dump(a.out/'records.json',aggregate);upload(a.out/'records.json',a.gcs_prefix)
 print(json.dumps({k:v for k,v in aggregate.items()if k!='records'}),flush=True)
if __name__=='__main__':main()
