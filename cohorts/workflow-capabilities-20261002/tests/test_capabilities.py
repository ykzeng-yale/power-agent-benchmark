#!/usr/bin/env python3
"""No provider calls. Real local R artifacts + tampered transport/evidence cases."""
import base64,copy,csv,hashlib,importlib.util,json,pathlib,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'runner'))
from score import score,check_png,check_csv
from dispatch import CORE,execute_job,sha,token_cost,make_request
from analyze import check_budget,apply_operational_contract
from redact_public import public_record

def load_oracle(id):return next(o for o in json.loads((ROOT/'audited/oracles.json').read_text())['tasks']if o['id']==id)
def artifact(name,b,eid):return {'artifact_id':'a-'+eid+'-'+name,'name':name,'size':len(b),'type':name.rsplit('.',1)[-1],'mime_type':'text/csv'if name.endswith('.csv')else'image/png','sha256':hashlib.sha256(b).hexdigest(),'execution_id':eid,'content_base64':base64.b64encode(b).decode()}

class CapabilityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory(prefix='pa-capability-actual-R-');td=pathlib.Path(cls.temp.name)
  cls.code='''d <- .42; alpha <- .04; target <- .85
pwr <- function(n) stats::power.t.test(n=n,delta=d,sd=1,sig.level=alpha,type="two.sample",alternative="two.sided",strict=TRUE)$power
n <- 2; while(pwr(n)<target) n <- n+1
n_grid <- seq(5,160,5); curve <- data.frame(n_per_arm=n_grid,total_n=2*n_grid,power=sapply(n_grid,pwr))
write.csv(curve,"sensitivity.csv",row.names=FALSE)
png("sensitivity.png",width=800,height=600)
plot(curve$n_per_arm,curve$power,type="b",xlab="Participants per arm",ylab="Power (probability)",main="Exact pooled two-sample t")
abline(h=target,lty=2);dev.off()
results <- list(list(metric="sample_size",value=n,unit="participants_per_arm"),list(metric="total_sample_size",value=2*n,unit="participants_total"),list(metric="achieved_power",value=pwr(n),unit="probability"),list(metric="preceding_power",value=pwr(n-1),unit="probability"))
cat("POWER_AGENT_RESULT=",jsonlite::toJSON(list(results=results),auto_unbox=TRUE,digits=15),"\\n",sep="")
'''
  p=subprocess.run(['Rscript','-e',cls.code],cwd=td,text=True,capture_output=True,check=True)
  computed=json.loads(next(line.split('=',1)[1]for line in p.stdout.splitlines()if line.startswith('POWER_AGENT_RESULT=')))
  cls.review_code='''n<-110;d<-.42;a<-.04;df<-2*n-2;nc<-d*sqrt(n/2);critical<-qt(1-a/2,df);power<-pt(critical,df,ncp=nc,lower.tail=FALSE)+pt(-critical,df,ncp=nc)
cat(jsonlite::toJSON(list(results=list(list(metric="achieved_power",value=power,unit="probability"))),auto_unbox=TRUE,digits=15))'''
  rp=subprocess.run(['Rscript','-e',cls.review_code],text=True,capture_output=True,check=True)
  files=[artifact(name,(td/name).read_bytes(),'e1')for name in ['sensitivity.csv','sensitivity.png']]
  coder={'id':'e1','role':'coder','phase':'solver','candidate_round':0,'success':True,'exitCode':0,'code':cls.code,'code_sha256':hashlib.sha256(cls.code.encode()).hexdigest(),'computed':computed,'output_files':files}
  reviewer={'id':'e2','role':'reviewer','phase':'verification','candidate_round':0,'success':True,'exitCode':0,'code':cls.review_code,'code_sha256':hashlib.sha256(cls.review_code.encode()).hexdigest(),'computed':json.loads(rp.stdout),'output_files':[]}
  source_url=load_oracle('wc26-pooled-t')['source_url'];content='Injected unit-test primary-source receipt. This is not a real provider retrieval.'
  sources=[{'id':sid,'url':source_url,'content':content,'content_sha256':hashlib.sha256(content.encode()).hexdigest(),'retrieved_at':'2026-10-02T00:00:00Z','content_scope':'provider_excerpt'if sid=='s1'else'provider_extracted_document_text'}for sid in ['s1','s2']]
  cls.good={'scientificStatus':'completed','status':'completed','success':True,'workflowMode':'single','verificationPolicy':'required','results':computed['results'],'design':load_oracle('wc26-pooled-t')['design'],'answer':{'results':computed['results'],'evidence_ids':['e1'],'citations':[{'url':source_url,'supports':'Injected testing only.'}]},'executions':[coder,reviewer],'review':{'verdict':'pass','independent_check_evidence_ids':['e2'],'checked_evidence_ids':['e1']},'verification':{'current_candidate_round':0},'sources':sources,'trace':[{'type':'search','source_ids':['s1']},{'type':'source_read','source_ids':['s2']}],'outputFiles':files}
  cls.oracle=load_oracle('wc26-pooled-t')
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_actual_R_numeric_CSV_PNG_evidence_validates(self):
  out=score(self.good,self.oracle);self.assertTrue(out['passed'],out['reasons']);self.assertEqual(out['artifact_details']['visual_scientific_content'],'pending_separate_blinded_rubric')
 def test_tampered_primary_count_and_units(self):
  for key,value in [('value',109),('unit','participants_total')]:
   r=copy.deepcopy(self.good);r['results'][0][key]=value;self.assertFalse(score(r,self.oracle)['passed'])
 def test_duplicate_metric_fails(self):
  r=copy.deepcopy(self.good);r['results'].append(copy.deepcopy(r['results'][0]));self.assertFalse(score(r,self.oracle)['passed'])
 def test_stale_coder_and_artifacts_rejected(self):
  r=copy.deepcopy(self.good);r['executions'][0]['candidate_round']=-1
  out=score(r,self.oracle);self.assertFalse(out['passed']);self.assertFalse(out['artifact_pass']);self.assertIn('coder_evidence_not_all_current_valid_unique',out['reasons'])
 def test_extra_stale_or_missing_reviewer_id_rejected(self):
  for stale in ['e-old','e-missing']:
   r=copy.deepcopy(self.good);r['review']['independent_check_evidence_ids'].append(stale)
   if stale=='e-old':
    e=copy.deepcopy(r['executions'][1]);e.update(id=stale,candidate_round=-1);r['executions'].append(e)
   out=score(r,self.oracle);self.assertFalse(out['passed']);self.assertIn('verification_not_all_current_valid_unique',out['reasons'])
 def test_review_must_cover_answer_evidence(self):
  r=copy.deepcopy(self.good);r['review']['checked_evidence_ids']=[]
  self.assertIn('review_does_not_cover_current_answer_evidence',score(r,self.oracle)['reasons'])
 def test_extra_current_coder_success_and_failure_allowed_for_inspection(self):
  for success in [True,False]:
   r=copy.deepcopy(self.good);extra=copy.deepcopy(r['executions'][0]);extra.update(id='e3',success=success,exitCode=0 if success else 1,output_files=[])
   r['executions'].append(extra);r['review']['checked_evidence_ids'].append('e3')
   out=score(r,self.oracle);self.assertTrue(out['passed'],out['reasons'])
 def test_inspection_rejects_stale_missing_wrongrole_duplicate_IDs(self):
  for bad in ['stale','missing','wrong_role','duplicate_checked','duplicate_execution']:
   r=copy.deepcopy(self.good);extra=copy.deepcopy(r['executions'][0]);extra.update(id='e3',output_files=[])
   if bad=='stale':extra['candidate_round']=-1
   if bad=='wrong_role':extra['role']='reviewer'
   if bad!='missing':r['executions'].append(extra)
   r['review']['checked_evidence_ids'].append('e3')
   if bad=='duplicate_checked':r['review']['checked_evidence_ids'].append('e3')
   if bad=='duplicate_execution':r['executions'].append(copy.deepcopy(extra))
   out=score(r,self.oracle);self.assertFalse(out['passed']);self.assertIn('checked_coder_inspection_not_all_current_valid_unique',out['reasons'])
 def test_failed_inspected_coder_cannot_ground_answer_or_artifacts(self):
  r=copy.deepcopy(self.good);r['executions'][0].update(success=False,exitCode=1)
  out=score(r,self.oracle);self.assertFalse(out['passed']);self.assertFalse(out['evidence_pass']);self.assertFalse(out['artifact_pass']);self.assertIn('coder_evidence_not_all_current_valid_unique',out['reasons'])
 def test_source_hash_document_search_and_order(self):
  changes=['hash','source','order','only_snippet']
  for change in changes:
   r=copy.deepcopy(self.good)
   if change=='hash':r['sources'][1]['content']+=' tampered'
   elif change=='source':r['sources'][0]['url']='https://stat.ethz.ch/unrelated'
   elif change=='order':r['trace'].reverse()
   else:r['sources'][1]['content_scope']='provider_excerpt'
   self.assertFalse(score(r,self.oracle)['source_pass'],change)
 def test_identical_document_receipt_dedup_requires_actual_extractor(self):
  r=copy.deepcopy(self.good);s=r['sources'][0];r['sources']=[s]
  r['trace']=[{'type':'search','source_ids':[s['id']]},{'type':'source_read','url':s['url'],'source_ids':[s['id']],'results':{'provider':'tavily_extract','url':s['url'],'results':[copy.deepcopy(s)]}}]
  out=score(r,self.oracle);self.assertTrue(out['source_pass']);self.assertTrue(out['source_receipt_annotations'][0]['identical_content_deduplicated_document_read']);self.assertEqual(s['content_scope'],'provider_excerpt')
  for bad in ['provider','hash','url']:
   q=copy.deepcopy(r)
   if bad=='provider':q['trace'][1]['results']['provider']='injected'
   elif bad=='hash':q['trace'][1]['results']['results'][0]['content_sha256']='0'*64
   else:q['trace'][1]['results']['url']+='wrong'
   self.assertFalse(score(q,self.oracle)['source_pass'],bad)
 def test_forged_artifact_digest_or_snapshot_cannot_pass(self):
  for modify in ['bytes','digest','snapshot']:
   r=copy.deepcopy(self.good)
   if modify=='bytes':r['outputFiles'][0]['content_base64']=base64.b64encode(b'forged').decode()
   elif modify=='digest':
    r['outputFiles'][0]['sha256']='a'*64;r['executions'][0]['output_files'][0]['sha256']='a'*64
   else:r['outputFiles'][0]['execution_id']='e-unrelated'
   self.assertFalse(score(r,self.oracle)['artifact_pass'],modify)
 def test_CSV_wrong_curve_duplicate_and_missing_grid(self):
  b=base64.b64decode(self.good['outputFiles'][0]['content_base64']);lines=b.decode().splitlines()
  for changed in [lines[:-1],lines+[lines[-1]],lines[:1]+[lines[1].rsplit(',',1)[0]+',0.999999']+lines[2:]]:
   ok,_,_=check_csv(('\n'.join(changed)+'\n').encode(),self.oracle['csv']);self.assertFalse(ok)
 def test_PNG_header_alone_and_corrupt_image_rejected(self):
  b=base64.b64decode(self.good['outputFiles'][1]['content_base64'])
  self.assertFalse(check_png(b[:33])[0]);self.assertFalse(check_png(b[:-20]+b'corrupted')[0])
 def test_null_provider_and_evaluation_drift_fail_closed(self):
  self.assertFalse(score(None,self.oracle)['passed'])
  r=copy.deepcopy(self.good);r['evaluation_version_changed']=True;self.assertFalse(score(r,self.oracle)['passed'])
 def test_missing_input_success_and_unwarranted_count(self):
  o=load_oracle('wc26-missing-cluster');r={'scientificStatus':'needs_clarification','success':False,'plan':{'ready':False,'missing_information':['ICC','participants per cluster'],'clarification_questions':['What ICC and mean participants per cluster?']},'results':[]}
  self.assertTrue(score(r,o)['passed']);r['results']=[{'metric':'sample_size','value':50,'unit':'participants_total'}];self.assertFalse(score(r,o)['passed']);r['results'][0]['unit']='kilograms';self.assertFalse(score(r,o)['passed'])
 def test_conditional_events_allowed_recruitment_forbidden(self):
  o=load_oracle('wc26-missing-survival');r={'scientificStatus':'needs_clarification','plan':{'ready':False,'missing_information':['event probability'],'clarification_questions':['What is the event probability or follow-up duration?']},'results':[{'metric':'conditional_events','value':150,'unit':'events'}]}
  self.assertTrue(score(r,o)['passed']);r['results'][0]['unit']='participants_total';self.assertFalse(score(r,o)['passed'])
 def test_final_capacity_profiles_identical_between_modes(self):
  p=json.loads((ROOT/'audited/profiles.json').read_text());payload=dict(p,tasks=[{'id':'fixture','query':'same scientific request'}])
  for name,totals,review in [('shared',(18,8,300000),(4,2)),('expanded',(26,12,540000),(5,3))]:
   requests=[make_request(payload,{'task_id':'fixture','profile':name,'mode':m})for m in ['single','multi']]
   self.assertEqual({k:v for k,v in requests[0].items()if k!='workflowMode'},{k:v for k,v in requests[1].items()if k!='workflowMode'})
   self.assertEqual(tuple(requests[0][k]for k in ['maxModelCalls','maxExecutions','deadlineMs']),totals)
   self.assertEqual(tuple(requests[0]['budgetProfile'][k]for k in ['verificationMaxCalls','verificationMaxExecutions']),review)
   self.assertEqual(requests[0]['verificationPolicy'],'required');self.assertTrue(requests[0]['budgetProfile']['reserveRepair'])
 def test_budget_profile_mismatch_rejected(self):
  p=json.loads((ROOT/'audited/profiles.json').read_text());request=dict(p['common'],**p['profiles']['shared'],workflowMode='single');r={'workflowMode':'single','verificationPolicy':'required','budget':{'global':{k:request[k]for k in ['maxModelCalls','maxExecutions','deadlineMs','maxSearches','maxSourceReads','maxSourceChars']},'profile':request['budgetProfile'],'used':{'model_calls':0,'executions':0,'searches':0,'source_reads':0,'source_chars':0},'phases':[]},'executions':[]}
  self.assertFalse(check_budget(r,request));r['budget']['global']['maxExecutions']=9;self.assertTrue(check_budget(r,request))
 def test_outer_runtime_changed_rejects_including_null(self):
  profiles=json.loads((ROOT/'audited/profiles.json').read_text());request=dict(profiles['common'],**profiles['profiles']['shared'],workflowMode='single')
  for record in [None,{'workflowMode':'single','verificationPolicy':'required','budget':{}}]:
   evaluation=apply_operational_contract({'passed':True,'reasons':[]},{'runtime_changed':True},record,request)
   self.assertFalse(evaluation['passed']);self.assertIn('runtime_changed_during_attempt',evaluation['reasons'])
 def test_raw_bytes_persist_before_invalid_JSON_parse(self):
  with tempfile.TemporaryDirectory()as td:
   td=pathlib.Path(td);cli=td/'scientific-harness-cli.js'
   for name in CORE:(td/name).write_text('fixture')
   cli.write_text('import sys\nsys.stdout.write("broken JSON")\nsys.stderr.write("fixture diagnostic")\n')
   expected={name:sha(td/name)for name in CORE};out=td/'out';job={'job_id':'fixture','mode':'single','task_id':'fixture','profile':'shared','repeat':1}
   r=execute_job(job,{'deadlineMs':1000},cli,sys.executable,out,'protocol-fixture',None,expected)
   raw=out/'transports/fixture.transport.json';self.assertTrue(raw.exists());transport=json.loads(raw.read_text());self.assertEqual(base64.b64decode(transport['stdout_base64']),b'broken JSON');self.assertIsNone(r['record']);self.assertEqual(r['capture_error'],'JSONDecodeError')
 def test_non_object_JSON_preserved_without_cost_crash(self):
  for response in ['[1]','42','null','"text"']:
   with tempfile.TemporaryDirectory()as td:
    td=pathlib.Path(td);cli=td/'scientific-harness-cli.js'
    for name in CORE:(td/name).write_text('fixture')
    cli.write_text('import sys\nsys.stdout.write('+repr(response)+')\n')
    expected={name:sha(td/name)for name in CORE};job={'job_id':'fixture','mode':'single','task_id':'fixture','profile':'shared','repeat':1}
    r=execute_job(job,{'deadlineMs':1000},cli,sys.executable,td/'out','protocol-fixture',None,expected)
    self.assertIsNone(r['record']);self.assertEqual(r['capture_error'],'ValueError');self.assertEqual(token_cost(r['record']),0)
    self.assertEqual(base64.b64decode(json.loads((td/'out/transports/fixture.transport.json').read_text())['stdout_base64']).decode(),response)
  self.assertEqual(token_cost([1]),0);self.assertEqual(token_cost({'usage':[]}),0)
 def test_whole64_invalid_nonobject_transport_is_accounted_and_scored(self):
  with tempfile.TemporaryDirectory(prefix='pa-capability-accounting-fixture-')as td:
   td=pathlib.Path(td);runtime=td/'runtime';runtime.mkdir()
   for name in CORE:(runtime/name).write_text('fixture')
   cli=runtime/'scientific-harness-cli.js';cli.write_text('print("[1]")\n')
   frozen=td/'frozen';run=td/'run'
   subprocess.run([sys.executable,str(ROOT/'runner/freeze.py'),'--runtime-dir',str(runtime),'--runtime-image','gcr.test/fixture@sha256:'+'0'*64,'--out',str(frozen)],capture_output=True,check=True)
   protocol=json.loads((frozen/'protocol.json').read_text());self.assertEqual(protocol['planned_attempts'],64);self.assertEqual(protocol['forecast_dispatch_limit_usd'],35);self.assertIn('tests/test_capabilities.py',protocol['frozen_evaluator_files'])
   subprocess.run([sys.executable,str(ROOT/'runner/dispatch.py'),'--cli',str(cli),'--node',sys.executable,'--questions',str(frozen/'public-questions.json'),'--protocol',str(frozen/'protocol.json'),'--out',str(run)],capture_output=True,check=True)
   subprocess.run([sys.executable,str(ROOT/'runner/analyze.py'),'--run',str(run)],capture_output=True,check=True)
   result=json.loads((run/'scored-results.json').read_text());self.assertEqual(result['planned_attempts'],64);self.assertEqual(len(result['records']),64);self.assertEqual(len(list((run/'transports').glob('*.json'))),64)
   self.assertTrue(all(r['record']is None and r['evaluation']['passed']is False and r['transport_captured']is True for r in result['records']))
 def test_public_projection_removes_source_repetitions_and_retains_numbers(self):
  r=copy.deepcopy(self.good);secret=' '.join('sourceword'+str(i)for i in range(200))
  r['sources'][0]['content']=secret;r['sources'][0]['content_sha256']=hashlib.sha256(secret.encode()).hexdigest()
  r['answer']['summary']=secret;r['trace'].append({'type':'tool_result','submitted_input':{'code':secret},'result':{'content':secret}})
  r['fullCode']=secret;r['executionOutput']=secret;r['verification']['rounds']=[{'round':0,'review':{'summary':secret}}];r['executions'][0]['code']+='# '+secret
  public=public_record(r);text=json.dumps(public);self.assertNotIn(secret,text);self.assertNotIn('sourceword199',text);self.assertEqual(public['results'],r['results']);self.assertEqual(public['sources'][0]['content_sha256'],r['sources'][0]['content_sha256']);self.assertTrue(public['executions'][0]['code_redacted_for_source_bulk']);self.assertNotIn('content_base64',text)
 def test_seventh_source_dependency_fingerprint(self):
  with tempfile.TemporaryDirectory()as td:
   td=pathlib.Path(td)
   for name in CORE:(td/name).write_text('fixture')
   old={name:sha(td/name)for name in CORE};(td/'scientific-sources.js').write_text('changed')
   self.assertNotEqual(old,{name:sha(td/name)for name in CORE});self.assertEqual(len(old),7)

if __name__=='__main__':unittest.main(verbosity=2)
