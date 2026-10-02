#!/usr/bin/env python3
import datetime,json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
rs=json.loads((ROOT/'validation/r-reference.json').read_text());rby={r['id']:r for r in rs['tasks']}
oracles=json.loads((ROOT/'audited/oracles.json').read_text());checks=[];maximum=0
for o in oracles['tasks']:
 if o['kind']!='calculation':continue
 r=rby[o['id']]
 for metric in o['results']:
  actual=r['values'][metric['metric']];delta=abs(actual-metric['value']);maximum=max(maximum,delta)
  checks.append(dict(task=o['id'],field=metric['metric'],python=metric['value'],R=actual,absolute_difference=delta,pass_=delta<=max(1e-9,metric['absolute_tolerance']/100)))
 for i,row in enumerate(o['csv']['rows']):
  for col,want in row.items():
   actual=r['rows'][i][col];delta=abs(actual-want);maximum=max(maximum,delta)
   checks.append(dict(task=o['id'],field=f'CSVrow{i+1}:{col}',absolute_difference=delta,pass_=delta<=max(1e-9,o['csv']['absolute_tolerances'][col]/100)))
 d=o['details']
 if 'published_sample_size'in d:
  actual=next(x['value'] for x in o['results'] if x['metric']=='sample_size')
  checks.append(dict(task=o['id'],field='published_integer_sample_size',pass_=actual==d['published_sample_size'],published=d['published_sample_size'],recomputed=actual))
 if 'published_required_events'in d:
  actual=next(x['value'] for x in o['results'] if x['metric']=='required_events')
  checks.append(dict(task=o['id'],field='published_integer_event_target',pass_=actual==d['published_required_events'],published=d['published_required_events'],recomputed=actual))
 if 'published_continuous_n'in d:
  checks.append(dict(task=o['id'],field='published_continuous_n_rounded',pass_=abs(d['continuous_n_per_group']-d['published_continuous_n'])<=d['published_tolerance']))
 if 'published_mde'in d:
  actual=next(x['value'] for x in o['results'] if x['metric']=='mde')
  checks.append(dict(task=o['id'],field='published_mde_rounded',pass_=abs(actual-d['published_mde'])<=d['published_tolerance']))
 # Required minima cross the threshold only under the declared computation.
 if o['id']!='wc26-open-cohort-sw':
  target=next(t['parameters']['target_power'] for t in json.loads((ROOT/'audited/tasks.json').read_text())['tasks'] if t['id']==o['id'])
  power=next(x['value'] for x in o['results'] if x['metric']=='achieved_power');preceding=next(x['value'] for x in o['results'] if x['metric']=='preceding_power')
  checks.append(dict(task=o['id'],field='minimum_threshold',pass_=power>=target and preceding<target))
out=dict(validation_version='workflow-capabilities-crosscheck1',checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),all_checks_pass=all(c['pass_'] for c in checks),check_count=len(checks),maximum_absolute_R_vs_Python_difference=maximum,R_runtime=rs['runtime'],python_runtime={k:oracles[k] for k in ['python_version','scipy_version','numpy_version']},independence_qualification='Different languages/statistical libraries for t/ANOVA. Cox formulas specified in same primary manual but evaluated independently. NIH uses projected treatment information in Python and full GLS normal-equation inverse in R; common scientific covariance assumptions remain shared.',checks=checks)
(ROOT/'validation/independent-verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},indent=2))
if not out['all_checks_pass']:raise SystemExit('Independent reference disagreement; stop before freeze.')
