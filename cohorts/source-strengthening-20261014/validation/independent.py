#!/usr/bin/env python3
"""Second implementation using SciPy distributions rather than R/pwr calls."""
import json,pathlib,math
from scipy.stats import t,nct,f,ncf,norm,chi2
ROOT=pathlib.Path(__file__).resolve().parents[1]
from scipy.integrate import quad
from scipy.special import expit,logit
def first(fn,target,start=2):
 for n in range(start,100001):
  v=fn(n)
  if not math.isfinite(v):raise ValueError(f'Nonfinite probability at design {n}')
  if v>=target:return n
 raise ValueError('No solution')
def riley(method,p):
 q,r,s=p['parameters'],p['rsquared'],p['shrinkage']
 if method=='riley_continuous':
  def shrink(n):return 1+(q-2)/(n*math.log1p(-(r*(n-q-1)+q)/(n-1)))
  n1=first(shrink,s,q+2);n2=math.ceil(1+q*(1-r)/p['rsquared_difference']);n3=first(lambda n:-math.sqrt(max(chi2.ppf(.975,n-q-1)/(n-q-1),(n-q-1)/chi2.ppf(.025,n-q-1))),-p['residual_sd_mmoe'],q+2);n=max(n1,n2,n3)
  while t.ppf(.975,n-q-1)*math.sqrt(p['sd']**2*(1-r)/n)>abs(p['intercept'])*(p['intercept_mmoe']-1):n+=1
  return n
 n1=math.ceil(q/((s-1)*math.log1p(-r/s)))
 if method=='riley_binary':pi=p['prevalence'];maxr=1-math.exp(2*(pi*math.log(pi)+(1-pi)*math.log1p(-pi)))
 else:e=math.ceil(p['rate']*p['meanfup']*10000);maxr=1-math.exp(2*(e*math.log(e/10000)-e)/10000)
 s2=r/(r+p['rsquared_difference']*maxr);n2=math.ceil(q/((s2-1)*math.log1p(-r/s2)))
 n3=math.ceil((1.96/p['risk_halfwidth'])**2*pi*(1-pi)) if method=='riley_binary' else first(lambda n:-(math.exp(-p['rate']*p['timepoint'])-math.exp(-(p['rate']+1.96*math.sqrt(p['rate']/(p['meanfup']*n)))*p['timepoint'])),-p['risk_halfwidth'])
 return max(n1,n2,n3)
def logistic_reference(p):
 b0=logit(p['event_probability_X0']);b1=logit(p['event_probability_X1'])-b0
 if p['predictor_distribution']=='normal':
  lo=p['predictor_mean']-12*p['predictor_sd'];hi=p['predictor_mean']+12*p['predictor_sd']
  moments=[quad(lambda x,j=j:x**j*expit(b0+b1*x)*(1-expit(b0+b1*x))*norm.pdf(x,p['predictor_mean'],p['predictor_sd']),lo,hi,epsabs=1e-12,epsrel=1e-12)[0] for j in range(3)]
  mu=quad(lambda x:expit(b0+b1*x)*norm.pdf(x,p['predictor_mean'],p['predictor_sd']),lo,hi,epsabs=1e-12,epsrel=1e-12)[0];varx=p['predictor_sd']**2
 else:
  px=p['predictor_binary_prevalence'];p0=p['event_probability_X0'];p1=p['event_probability_X1'];moments=[(1-px)*p0*(1-p0)+px*p1*(1-p1),px*p1*(1-p1),px*p1*(1-p1)];mu=(1-px)*p0+px*p1;varx=px*(1-px)
 i0,i1,i2=moments;v1=i0/(i0*i2-i1*i1);v0=1/(varx*mu*(1-mu));aa=p['variance_correction_a'];sd=math.sqrt((aa*v0+(1-aa)*v1)/v1);sides=2 if p['alternative']=='two_sided' else 1;z=norm.ppf(1-p['alpha']/sides)
 def pw(n):
  mu1=b1*math.sqrt(n*(1-p['r2_other_X'])/v1)
  return norm.sf((z-mu1)/sd)+(norm.cdf((-z-mu1)/sd) if sides==2 else 0)
 n=first(pw,p['power'],1)
 return dict(value=n,achieved_power=pw(n),preceding_power=pw(n-1),v1=v1,v0=v0,mean_event_probability=mu,variance_correction_a=aa)
def calculate(s):
 p,m=s['parameters'],s['method'];a=p.get('alpha',.05)
 if m.startswith('riley'):return riley(m,p)
 if m=='logistic_demidenko_variance_corrected':return logistic_reference(p)['value']
 if m=='cluster_rate_cv':return math.ceil(1+(norm.ppf(.975)+norm.ppf(p['power']))**2*((p['r1']+p['r2'])/p['exposure']+p['cv']**2*(p['r1']**2+p['r2']**2))/(p['r1']-p['r2'])**2)
 if m=='proportion_precision':return math.ceil(norm.ppf(1-a/2)**2*p['p']*(1-p['p'])/p['margin']**2)
 def fp(N,u,v,f2):return 1-ncf.cdf(f.isf(a,u,v),u,v,N*f2)
 def fn(n):
  if m in ['one_sample_t','two_sample_t','paired_t']:
   two=m=='two_sample_t';df=2*n-2 if two else n-1;nc=p['d']*math.sqrt(n/2 if two else n);sides=2 if s['expected_design']['alternative']=='two_sided' else 1;crit=t.isf(a/sides,df)
   return 1-nct.cdf(crit,df,nc)+(nct.cdf(-crit,df,nc) if sides==2 else 0)
  if m=='linear_regression':return fp(n,p['u'],n-p['p']-1,p['f2'])
  if m=='one_way_anova':N=n if s['metric']=='power' else n*p['groups'];return fp(N,p['groups']-1,N-p['groups'],p['f2'])
  if m=='factorial_anova':N=n*p['cells'];return fp(N,p['u'],N-p['cells'],p['f2'])
  if m=='rm_between':return fp(2*n,1,2*n-2,p['f2']*p['measurements']/(1+(p['measurements']-1)*p['rho']))
  if m=='rm_within':return fp(n,(p['measurements']-1)*p['epsilon'],(n-1)*(p['measurements']-1)*p['epsilon'],p['f2']*p['measurements']/(1-p['rho'])*p['epsilon'])
  if m=='rm_interaction':return fp(2*n,(p['measurements']-1)*p['epsilon'],(2*n-2)*(p['measurements']-1)*p['epsilon'],p['f2']*p['measurements']/(1-p['rho'])*p['epsilon'])
  raise ValueError(m)
 return fn(p['n']) if s['metric']=='power' else first(fn,p['power'],p['p']+2 if m=='linear_regression' else 2)
if __name__=='__main__':
 import scipy,sys
 root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT
 output=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else root/'reproduction-output/python-reference.json'
 specs=json.loads((root/'audited/reference-specifications.json').read_text());rows=[]
 for s in specs:
  row=dict(id=s['id'],value=float(calculate(s)),metric=s['metric'],unit=s['unit'])
  if s['method']=='logistic_demidenko_variance_corrected':row['logistic_diagnostics']=logistic_reference(s['parameters'])
  rows.append(row)
 output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('x') as f:json.dump(dict(scipy_version=scipy.__version__,tasks=rows),f,indent=2);f.write('\n')
 print('Computed',len(rows),'independent SciPy reference results')
