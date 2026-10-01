import unittest,importlib.util,pathlib,copy,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('benchmark',ROOT/'runner/audited_benchmark.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Scoring(unittest.TestCase):
 def setUp(self):
  self.oracle=next(o for o in json.loads((ROOT/'audited/oracles.json').read_text())['tasks'] if o['id']=='pa26-t1-two-sample-n')
  results=[{'metric':'sample_size','value':42,'unit':'participants_per_group'}];code='x <- 2*21\n'
  self.record={'status':'completed','success':True,'results':results,'design':{'method':'two_sample_t','alternative':'one-sided','alpha':.05,'allocation_ratio':1},'executions':[{'role':'coder','success':True,'exitCode':0,'computed':{'results':copy.deepcopy(results)},'code':code,'code_sha256':hashlib.sha256(code.encode()).hexdigest()}]}
 def test_correct(self):self.assertTrue(b.score(self.record,self.oracle)['passed'])
 def test_wrong_unit_even_with_correct_number(self):
  self.record['results'][0]['unit']='participants_total';self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_correct_number_wrong_test(self):
  self.record['design']['alternative']='two-sided';self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_no_round_down_flexibility(self):
  self.record['results'][0]['value']=41;self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_nonfinite_rejected(self):
  self.record['results'][0]['value']=float('nan');self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_ambiguous_metric_rejected(self):
  self.record['results'].append(self.record['results'][0]);self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_no_output_is_failure(self):self.assertFalse(b.score({'status':'budget_exhausted','success':False},self.oracle)['passed'])
 def test_execution_claim_cannot_replace_evidence(self):
  self.record['executions']=[];self.record['evidence']={'executed':True};self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_unlinked_result_rejected(self):
  self.record['executions'][0]['computed']['results'][0]['value']=41;self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_execution_hash_mismatch_rejected(self):
  self.record['executions'][0]['code_sha256']='0'*64;self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_version_changed_rejected(self):
  self.record['evaluation_version_changed']=True;self.assertFalse(b.score(self.record,self.oracle)['passed'])
 def test_answer_not_sent(self):
  task=next(t for t in json.loads((ROOT/'audited/tasks.json').read_text())['tasks'] if t['id']==self.oracle['id']);req=b.public_request(task,'single');encoded=json.dumps(req)
  for secret in ['expected_value','source_answer','ground_truth',task['id'],'42']:
   self.assertNotIn(secret,encoded)
 def test_no_success_selection_in_denominator(self):
  task={'id':'t','tier':1};rows=[{'task_id':'t','mode':'single','repeat':i,'duration_seconds':1,'record':r,'evaluation':b.score(r,self.oracle)}for i,r in enumerate([self.record,{},{}])];s=b.summarize(rows,[task])['single'];self.assertEqual(s['planned_attempts'],3);self.assertAlmostEqual(s['pass_rate'],1/3)
 def test_source_family_split(self):
  families={}
  for t in json.loads((ROOT/'audited/tasks.json').read_text())['tasks']:families.setdefault(t['family'],set()).add(t['split'])
  self.assertTrue(all(len(s)==1 for s in families.values()))
 def test_all_twenty_have_oracles(self):
  tasks=json.loads((ROOT/'audited/tasks.json').read_text())['tasks'];oracles=json.loads((ROOT/'audited/oracles.json').read_text())['tasks'];self.assertEqual({t['id']for t in tasks},{o['id']for o in oracles});self.assertEqual(len(tasks),20)
if __name__=='__main__':unittest.main()
