"""Compare two saved reference outputs without executing R or model calls."""
import json, math, pathlib, sys
root=pathlib.Path(__file__).resolve().parents[1]
rpath=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else root/'validation/r-reference-observed.json'
ppath=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else root/'validation/python-reference-observed.json'
r=json.loads(rpath.read_text());p=json.loads(ppath.read_text())
specs=json.loads((root/'audited/reference-specifications.json').read_text())
rb={x['id']:x for x in r['tasks']};pb={x['id']:x for x in p['tasks']}
assert set(rb)==set(pb)=={s['id'] for s in specs}
checks=[]
for s in specs:
 a,b=rb[s['id']],pb[s['id']]
 assert math.isfinite(a['value']) and math.isfinite(b['value'])
 assert a['value']==b['value'] and a['unit']==b['unit']==s['unit']
 if s['published_source_value'] is not None:
  assert a['value']==s['published_source_value']
 if s['method'].startswith('riley'):
  assert a['source_value'] is None and a['package_match'] is True
 if s['method']=='logistic_demidenko_variance_corrected':
  ad,bd=a['logistic_diagnostics'],b['logistic_diagnostics']
  for key in ['achieved_power','preceding_power','v1','v0','mean_event_probability','variance_correction_a']:
   assert math.isfinite(ad[key]) and math.isfinite(bd[key])
   assert abs(ad[key]-bd[key])<=1e-10
  assert ad['achieved_power']>=s['parameters']['power']>ad['preceding_power']
  for key,c in s['additional_metrics'].items():
   assert abs(ad[key]-c['value'])<=c['absolute_tolerance']
 checks.append(dict(id=s['id'],R_value=a['value'],Python_value=b['value'],unit=s['unit'],agrees=True))
print(json.dumps(dict(status='14_OF_14_REFERENCE_RESULTS_AGREE',R=r['R'],scipy_version=p['scipy_version'],tasks=checks),indent=2))
