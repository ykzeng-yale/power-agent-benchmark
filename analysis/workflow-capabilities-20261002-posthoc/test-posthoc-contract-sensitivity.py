#!/usr/bin/env python3
"""Synthetic contract tampering fixtures; local R fixture, no providers.

All source and extra-review receipts in these tests are explicitly injected.
They are not scientific model responses or empirical retrieval evidence.
"""
from pathlib import Path
import base64,copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile,unittest

HERE=Path(__file__).resolve().parent
REPO=Path(os.environ.get('POWER_AGENT_BENCHMARK_REPO',str(Path(__file__).resolve().parents[2])))
SCORER=REPO/'cohorts/workflow-capabilities-20261002/runner/score.py'
spec=importlib.util.spec_from_file_location('posthoc',HERE/'posthoc-contract-sensitivity.py');posthoc=importlib.util.module_from_spec(spec);spec.loader.exec_module(posthoc)
spec=importlib.util.spec_from_file_location('frozen_fixture',REPO/'cohorts/workflow-capabilities-20261002/tests/test_capabilities.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.CapabilityTests.setUpClass();cls.oracle=fixture.CapabilityTests.oracle
        cls.good=copy.deepcopy(fixture.CapabilityTests.good)
        query='Injected search fixture; not an empirical provider request.'
        cls.good['source_requests']=[{'tool':'search_sources','success':True,'query':query,'provider':'tavily'}]
        cls.good['trace'][0].update(query=query,results={'provider':'tavily'})
        for f in cls.good['outputFiles']:
            if f['type']=='png':f['name']='sensitivity_plot.png'
        extra=copy.deepcopy(cls.good['executions'][1]);extra.update(id='e3',computed=None,code='stopifnot(TRUE)',code_sha256=hashlib.sha256(b'stopifnot(TRUE)').hexdigest())
        cls.good['executions'].append(extra);cls.good['review']['independent_check_evidence_ids'].append('e3')
        cls.good['results']=copy.deepcopy(cls.good['results']);cls.good['answer']['results']=cls.good['results'];cls.good['results'][2]['value']+=5e-10
        cls.combined,_=posthoc.fresh_scorer(['search_chain','review_IDs','figure_basename','grounding_precision'],SCORER)
    @classmethod
    def tearDownClass(cls):fixture.CapabilityTests.tearDownClass()
    def score(self,record):return self.combined.score(record,self.oracle)
    def test_positive_combined_contract_and_original_still_rejects(self):
        self.assertTrue(self.score(self.good)['passed'])
        original,_=posthoc.fresh_scorer([],SCORER);self.assertFalse(original.score(self.good,self.oracle)['passed'])
    def test_invalid_metric_unit_and_scientific_answer_not_excused(self):
        for field,value in [('metric','unrequested_name'),('unit','kilograms'),('value',109)]:
            r=copy.deepcopy(self.good);r['results'][0][field]=value
            if field=='value':r['executions'][0]['computed']['results'][0]['value']=value
            self.assertFalse(self.score(r)['passed'],field)
    def test_grounding_relative_tolerance_is_bounded(self):
        r=copy.deepcopy(self.good);r['results'][2]['value']+=5e-8
        out=self.score(r);self.assertTrue(out['numeric_pass']);self.assertFalse(out['evidence_pass'])
    def test_read_hash_citation_success_and_order_still_required(self):
        for change in ['hash','citation','failed_search','order','timestamp','scope']:
            r=copy.deepcopy(self.good)
            if change=='hash':r['sources'][1]['content']+='tampered'
            elif change=='citation':r['answer']['citations']=[]
            elif change=='failed_search':r['source_requests'][0]['success']=False
            elif change=='order':r['trace'].reverse()
            elif change=='timestamp':r['sources'][1]['retrieved_at']='invalid'
            else:r['sources'][1]['content_scope']='provider_excerpt'
            self.assertFalse(self.score(r)['source_pass'],change)
    def test_empty_successful_search_is_attempt_not_discovery(self):
        r=copy.deepcopy(self.good);r['trace'][0]['source_ids']=[]
        self.assertTrue(self.score(r)['source_pass'])
        original,_=posthoc.fresh_scorer([],SCORER);self.assertFalse(original.score(r,self.oracle)['source_pass'])
    def test_stale_missing_wrongrole_failed_duplicate_review_IDs_rejected(self):
        for bad in ['stale','missing','wrongrole','failed','duplicate']:
            r=copy.deepcopy(self.good)
            if bad=='stale':r['executions'][2]['candidate_round']=-1
            elif bad=='missing':r['review']['independent_check_evidence_ids'].append('missing')
            elif bad=='wrongrole':r['executions'][2]['role']='coder'
            elif bad=='failed':r['executions'][2].update(success=False,exitCode=1)
            else:r['review']['independent_check_evidence_ids'].append('e3')
            self.assertFalse(self.score(r)['evidence_pass'],bad)
    def test_review_requires_at_least_one_actual_current_numeric_check(self):
        r=copy.deepcopy(self.good);r['executions'][1]['computed']=None
        self.assertFalse(self.score(r)['evidence_pass'])
    def test_stale_failed_or_uncited_coder_never_grounds_numbers_or_files(self):
        for bad in ['stale','failed','uncited','hash']:
            r=copy.deepcopy(self.good)
            if bad=='stale':r['executions'][0]['candidate_round']=-1
            elif bad=='failed':r['executions'][0].update(success=False,exitCode=1)
            elif bad=='uncited':r['answer']['evidence_ids']=[]
            else:r['executions'][0]['code_sha256']='0'*64
            out=self.score(r);self.assertFalse(out['evidence_pass'],bad);self.assertFalse(out['artifact_pass'],bad)
    def test_forged_artifact_hash_claim_snapshot_and_format_rejected(self):
        for bad in ['hash','claim','bytes','format']:
            r=copy.deepcopy(self.good)
            if bad=='hash':r['outputFiles'][1]['sha256']='a'*64
            elif bad=='claim':r['outputFiles'][1]['execution_id']='uncited'
            elif bad=='bytes':r['outputFiles'][1]['content_base64']=base64.b64encode(b'forged').decode()
            else:r['outputFiles'][1]['mime_type']='text/plain'
            self.assertFalse(self.score(r)['artifact_pass'],bad)
    def test_correct_companion_dataset_not_supplied_or_repaired(self):
        r=copy.deepcopy(self.good);csv=r['outputFiles'][0];raw=base64.b64decode(csv['content_base64']);lines=raw.decode().splitlines();lines[1]=lines[1].rsplit(',',1)[0]+',.99999';changed=('\n'.join(lines)+'\n').encode()
        csv.update(size=len(changed),sha256=hashlib.sha256(changed).hexdigest(),content_base64=base64.b64encode(changed).decode())
        self.assertFalse(self.score(r)['artifact_pass'])
    def test_operational_budget_and_runtime_drift_never_relaxed(self):
        sys.path.insert(0,str(SCORER.parent));import analyze
        p=json.loads((SCORER.parent.parent/'audited/profiles.json').read_text());req=dict(p['common'],**p['profiles']['shared'],workflowMode='single')
        r=copy.deepcopy(self.good);r['budget']={'global':{k:req[k]for k in['maxModelCalls','maxExecutions','deadlineMs','maxSearches','maxSourceReads','maxSourceChars']},'profile':req['budgetProfile'],'used':{'model_calls':0,'executions':len(r['executions']),'searches':1,'source_reads':1,'source_chars':1},'phases':[]}
        self.assertTrue(analyze.apply_operational_contract(self.score(r),{},r,req)['passed'])
        self.assertFalse(analyze.apply_operational_contract(self.score(r),{'runtime_changed':True},r,req)['passed'])
        r['budget']['used']['executions']=9;self.assertFalse(analyze.apply_operational_contract(self.score(r),{},r,req)['passed'])
    def test_portable_cli_and_existing_output_refusal(self):
        r=subprocess.run([sys.executable,str(HERE/'posthoc-contract-sensitivity.py'),'--help'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0);self.assertIn('--repo',r.stdout);self.assertIn('--run',r.stdout);self.assertIn('--out',r.stdout)
        with tempfile.TemporaryDirectory()as td:
            sentinel=Path(td)/'posthoc-contract-sensitivity.json';sentinel.write_text('preserve')
            r=subprocess.run([sys.executable,str(HERE/'posthoc-contract-sensitivity.py'),'--repo',str(REPO),'--run','/definitely-missing','--out',td],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('Refuse overwrite',r.stderr);self.assertEqual(sentinel.read_text(),'preserve')

if __name__=='__main__':unittest.main(verbosity=2)
