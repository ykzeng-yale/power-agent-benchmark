#!/usr/bin/env python3
"""Execute legacy references without silently repairing them; never evaluate agents."""
import json, pathlib, subprocess, tempfile, concurrent.futures, hashlib, datetime, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
PRIMARY=['per_cell','patients_per_cluster','subjects_per_cluster','subjects_per_cluster_period','students_per_classroom','subjects_per_group','subjects_per_arm','sample_size_per_group','sample_size','subjects','total_sample_size','total_subjects','detectable_effect_d','detectable_effect_size','power']
KNOWN={
 't2-surv-005':'Two-arm Schoenfeld reference omits 1/[allocation*(1-allocation)] = 4. Its 62 events are a continuous-predictor calculation, not a two-arm log-rank design. Accrual is also unspecified.',
 't2-logreg-006':'Interaction reference substitutes two risks into a main-effect logistic formula. Earlier local simulation report recommends 1350, current ground truth 319 and reference comment 370; cannot certify interaction power.',
 't2-mixed-008':'Reference reduces a multivariate model to one averaged outcome without specifying estimand or multivariate test; conflicts with earlier local simulation report 140/group.',
 't3-cross-004':'Prompt says bioequivalence but provides no equivalence margins. A superiority paired t test cannot answer this question.',
 't3-simr-003':'Reference explicitly averages powers from z, likelihood-ratio and Kenward–Roger tests (36.5%, 30%, 26%). These are different procedures, not one ground truth.',
 't3-simr-004':'Reference gives different test-specific powers (63%,57%,54%) and uses their midpoint. Test and randomization level must be fixed.',
 't2-surv-008':'Strata weights and stratum event distributions unspecified; control risk substituted for pooled event probability.',
 't3-cluster-003':'Variable-cluster design effect incorrectly multiplies the equal-size DE by (1+CV²); standard approximation is 1+[((1+CV²)m)-1]ICC.',
 't2-poisson-006':'10% yearly increase is encoded as linear 1+0.1t, whereas multiplicative annual growth gives a different integrated rate; prompt must specify rate function.',
 't2-poisson-007':'Wald reference double-counts baseline rate: sqrt(effective events) and inverse rate variance are both used. Exact clustered count model/test also unspecified.',
 't1-anova-004':'Reference rounds f to .312 before solving although prompt group means imply sqrt(mean squared deviation)/20; integer may change.',
 't1-ttest-004':'Reference rounds 8/12 to .667 before solving; clean task must use exact supplied means and SD.',
}
def audit(t):
 code=t.get('reference_code',''); gt=t['ground_truth']; key=next((k for k in PRIMARY if k in gt),None)
 noncomments='\n'.join(x for x in code.splitlines() if x.strip() and not x.lstrip().startswith('#'))
 calculation=bool(re.search(r'(pwr\.|pwrss\.|power\.|pmsampsize\(|pmvalsampsize\(|powerSim\(|powerCurve\(|N\s*<-\s*ceiling)',noncomments))
 row={'id':t['id'],'tier':t['tier'],'template':t['template'],'primary_field':key,'legacy_value':gt.get(key),'legacy_tolerance':t.get('tolerance'), 'source_claim':t.get('source'), 'reference_sha256':hashlib.sha256(code.encode()).hexdigest(), 'published_example_verified':False, 'notes':[]}
 if t['id'] in KNOWN:row['notes'].append(KNOWN[t['id']])
 if not calculation:
  row['execution_status']='no_executable_calculation'; row['scientific_status']='quarantine'; row['notes'].append('Reference contains no executable power/sample-size calculation; library imports and prose are not validation.'); return row
 # Only execute supplied code, capture every evaluated list object, including assignments.
 wrapper='''args<-commandArgs(TRUE); code<-readLines(args[1],warn=FALSE); values<-list(); err<-NULL
tryCatch({for(expr in parse(text=code)){v<-eval(expr,envir=.GlobalEnv);if(is.list(v))values[[length(values)+1]]<-v}},error=function(e)err<<-conditionMessage(e))
keep<-lapply(values,function(v){v[sapply(v,function(z)is.numeric(z)&&length(z)==1)]});if(exists("N")&&is.numeric(N)&&length(N)==1)keep[[length(keep)+1]]<-list(N=N)
cat("AUDIT_JSON:",jsonlite::toJSON(list(error=err,values=keep,R=R.version.string),auto_unbox=TRUE,null="null"),"\\n",sep="")
'''
 try:
  with tempfile.TemporaryDirectory() as td:
   pathlib.Path(td,'ref.R').write_text(code);pathlib.Path(td,'audit.R').write_text(wrapper)
   out=subprocess.run(['Rscript',str(pathlib.Path(td,'audit.R')),str(pathlib.Path(td,'ref.R'))],capture_output=True,text=True,timeout=45)
  marker=out.stdout.rsplit('AUDIT_JSON:',1); d=json.loads(marker[1]) if len(marker)==2 else {'error':out.stderr[:800] or 'no audit output','values':[]}
  row['reference_execution']=d;row['execution_status']='error' if d.get('error') else 'executed'
  vals=d.get('values',[]);result=vals[-1] if vals else {};actual=None
  if key and key.startswith('detectable'):actual=result.get('d')
  elif key=='power':actual=result.get('power')
  elif t['template']=='linear_regression' and 'v' in result:
   p=gt.get('predictors',7 if t['id']=='t2-linreg-003' else gt.get('predictors_tested',result.get('u',0)));actual=__import__('math').ceil(result['v']+p+1)
  else:
   actual=next((result[k] for k in ['sample_size','n','N','total.n'] if k in result),None)
   if actual is not None:
    if t['id'] in ['t2-poisson-001','t2-poisson-002']:actual=actual/2;row['unit_transformation']='pwrss total n divided by 2 for equal groups'
    actual=__import__('math').ceil(actual)
  row['recomputed_primary']=actual
  row['numeric_match']=actual==gt.get(key) if actual is not None else None
  row['scientific_status']='quarantine' if d.get('error') or actual is None or row['notes'] or not row['numeric_match'] else 'numeric_reproduced_source_unverified'
  if actual is not None and actual!=gt.get(key):row['notes'].append('Supplied executable reference does not reproduce stored primary answer under installed R packages.')
 except Exception as e:row['execution_status']='error';row['scientific_status']='quarantine';row['notes'].append(str(e))
 return row
if __name__=='__main__':
 tasks=[]
 for tier in range(1,5):
  for t in json.loads((ROOT/f'tasks/tier{tier}/tasks.json').read_text())['tasks']:tasks.append(dict(t,tier=tier))
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(audit,tasks))
 from collections import Counter
 result={'audit_date':'2026-10-01','scope':'106 legacy tasks; execution checks are not independent source verification','counts':dict(Counter(r['scientific_status'] for r in rows)),'execution_counts':dict(Counter(r['execution_status'] for r in rows)), 'tasks':rows}
 (ROOT/'validation/legacy-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 lines=['# Legacy 106-task audit','', 'Every legacy task is excluded from the new primary suite until source/design verification. Executable reproduction alone does not establish scientific validity.','', '| ID | Execution | Stored → recomputed | Status | Findings |','|---|---|---|---|---|']
 for r in rows:lines.append(f"| {r['id']} | {r['execution_status']} | {r['legacy_value']} → {r.get('recomputed_primary','—')} | {r['scientific_status']} | {' '.join(r['notes']).replace('|','/')} |")
 (ROOT/'validation/legacy-audit.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='tasks'},indent=2))
