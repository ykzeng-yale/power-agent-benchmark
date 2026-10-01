#!/usr/bin/env python3
"""Second implementation: SciPy distributions, independently specified formulas."""
import json, math, pathlib
import scipy
from scipy.stats import norm
ROOT=pathlib.Path(__file__).resolve().parents[1]
specs=json.loads((ROOT/'audited/reference-specifications.json').read_text())
oracles={r['id']:r for r in json.loads((ROOT/'audited/oracles.json').read_text())['tasks']}
rows=[]
for s in specs:
    p=s['parameters']
    if s['method']=='logrank_freedman':
        if s['metric']=='power':
            value=float(norm.cdf(math.sqrt(p['n']*(p['pE']+p['pC']))*abs(p['HR']-1)/(p['HR']+1)-norm.ppf(.975)))
        else:
            value=math.ceil(((p['HR']+1)/(p['HR']-1))**2*(norm.ppf(.975)+norm.ppf(p['power']))**2/(p['pE']+p['pC']))
    elif s['method']=='cluster_rate_cv':
        value=math.ceil(1+(norm.ppf(.975)+norm.ppf(p['power']))**2*((p['r1']+p['r2'])/p['exposure']+p['cv']**2*(p['r1']**2+p['r2']**2))/(p['r1']-p['r2'])**2)
    else:
        raise ValueError(s['method'])
    error=abs(value-oracles[s['id']]['value'])
    rows.append({'id':s['id'],'scipy_value':value,'R_value':oracles[s['id']]['value'],'absolute_difference':error,'verified':error<1e-12})
result={'scipy_version':scipy.__version__,'all_verified':all(r['verified']for r in rows),'tasks':rows}
(ROOT/'validation/independent-verification.json').write_text(json.dumps(result,indent=2)+'\n')
assert result['all_verified']
print(result)
