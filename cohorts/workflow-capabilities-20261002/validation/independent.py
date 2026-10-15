#!/usr/bin/env python3
"""Evaluator-only Python/SciPy oracle. Never import or mount in model workspace."""
import json,math,pathlib,sys
import numpy as np
import scipy
from scipy import stats,optimize
ROOT=pathlib.Path(__file__).resolve().parents[1]
def t_power(n,d,alpha,paired=False):
 df=n-1 if paired else 2*n-2
 nc=d*math.sqrt(n if paired else n/2)
 c=stats.t.isf(alpha/2,df)
 return float(stats.nct.sf(c,df,nc)+stats.nct.cdf(-c,df,nc))
def minimum(fn,target,lower=2,step=1):
 for n in range(lower,1000000,step):
  if fn(n)>=target:return n
 raise ValueError('Design search exceeded documented bound')
def anova_power(n,means,wvar,alpha):
 q=len(means);df1=q-1;df2=q*(n-1)
 nc=n*sum((float(x)-np.mean(means))**2 for x in means)/wvar
 return float(stats.ncf.sf(stats.f.isf(alpha,df1,df2),df1,df2,nc))
def cox_events(beta,sd,r2,alpha,target,onesided):
 z=stats.norm.isf(alpha/(1 if onesided else 2))+stats.norm.ppf(target)
 return float(z*z/(sd*sd*beta*beta*(1-r2)))
def cox_power(n,eventp,beta,sd,r2,alpha,onesided):
 # Exact reproduction of the documented asymptotic one-tail Phi approximation,
 # including for a two-sided significance threshold; not a finite-sample certificate.
 return float(stats.norm.cdf(abs(beta)*sd*math.sqrt(n*eventp*(1-r2))-stats.norm.isf(alpha/(1 if onesided else 2))))
def sw_variance(p,g):
 t=p['periods'];lag=np.abs(np.arange(t)[:,None]-np.arange(t)[None,:])
 group=p['icc']*p['variance']*(1-p['group_r_squared'])
 member=(1-p['icc'])*p['variance']*(1-p['member_r_squared'])/p['members_per_cluster_period']
 V=group*np.power(p['cac'],lag)+member*(1-p['pairwise_churn'])*np.power(p['iac'],lag)
 np.fill_diagonal(V,group+member)
 W=np.linalg.inv(V);xs=np.asarray(p['treatment_sequences'],dtype=float)
 summed=xs.sum(axis=0)
 information=sum(x@W@x for x in xs)-summed@W@summed/len(xs)
 return float(1/(g*information)),V.tolist()
def sw_row(p,g):
 var,_=sw_variance(p,g);df=g*p['sequences']-p['periods']-1-p['group_covariate_df']
 mde=math.sqrt(var)*(stats.t.isf(p['alpha']/2,df)+stats.t.ppf(p['target_power'],df))
 return dict(clusters_per_sequence=g,total_clusters=g*p['sequences'],degrees_of_freedom=df,treatment_variance=var,mde=float(mde))
def row_result(metric,value,unit,integer=False):
 tol=0 if integer else (1e-8 if metric in ['treatment_variance'] else 1e-6 if 'power' in metric or metric=='mde' else max(1e-6,abs(value)*1e-6))
 return dict(metric=metric,value=int(value) if integer else float(value),unit=unit,integer=integer,absolute_tolerance=tol)
def oracle(task):
 p=task['parameters'];id=task['id'];rows=[];values={};details={}
 if task['outcome_kind']=='clarification':
  topics=[['intracluster','intra.cluster','ICC'],['cluster size','participants per cluster','members per cluster']] if id.endswith('cluster') else [['event probability','probability of.*event','event rate','follow.up','accrual','censor']]
  return dict(id=id,kind='clarification',topics=topics,forbidden_count_units=['participants_total','participants_per_arm','participants_per_group','clusters_total','clusters_per_arm','clusters_per_group'],conditional_events_allowed=id.endswith('survival'),requires_sources=False,requires_artifacts=False)
 if id=='wc26-pooled-t':
  fn=lambda n:t_power(n,p['d'],p['alpha']);n=minimum(fn,p['target_power'])
  values={'sample_size':n,'total_sample_size':2*n,'achieved_power':fn(n),'preceding_power':fn(n-1)}
  rows=[dict(n_per_arm=k,total_n=2*k,power=fn(k)) for k in p['grid_n']]
  continuous=optimize.brentq(lambda x:fn(x)-p['target_power'],2,n+1,xtol=1e-11)
  details={'continuous_n_per_arm':continuous,'ncp_definition':'d*sqrt(n_per_arm/2)','both_rejection_tails':True}
 elif id=='wc26-paired-t':
  for rho in p['rho_grid']:
   sd=p['measurement_sd']*math.sqrt(2*(1-rho));fn=lambda n:t_power(n,p['mean_difference']/sd,p['alpha'],True);n=minimum(fn,p['target_power'])
   row=dict(rho=rho,difference_sd=sd,n_pairs=n,achieved_power=fn(n),preceding_power=fn(n-1));rows.append(row)
   if rho==p['rho']:values={'sample_size':n,'difference_sd':sd,'achieved_power':fn(n),'preceding_power':fn(n-1)}
  details={'ncp_definition':'mean_difference/difference_sd*sqrt(n_pairs)','difference_sd_definition':'measurement_sd*sqrt(2*(1-rho))'}
 elif id=='wc26-anova':
  fn=lambda n:anova_power(n,p['group_means'],p['within_variance'],p['alpha']);n=minimum(fn,p['target_power'])
  values={'sample_size':n,'total_sample_size':p['groups']*n,'achieved_power':fn(n),'preceding_power':fn(n-1)}
  rows=[dict(n_per_group=k,total_n=p['groups']*k,power=fn(k)) for k in p['grid_n']]
  details={'between_var_sample_variance':float(np.var(p['group_means'],ddof=1)),'continuous_n_per_group':float(optimize.brentq(lambda x:fn(x)-p['target_power'],2,n+1)),'published_continuous_n':15.18834,'published_tolerance':.00001,'published_source_locator':'power.anova.test Examples anticipated group means 120,130,140,150'}
 elif id in ['wc26-cox-binary','wc26-cox-continuous']:
  binary=id.endswith('binary');onesided=not binary;sd=.5 if binary else p['covariate_sd']
  for a in (p['hr_grid'] if binary else p['r2_grid']):
   beta=math.log(a) if binary else p['beta'];r2=0 if binary else a
   ev=cox_events(beta,sd,r2,p['alpha'],p['target_power'],onesided)
   for eventp in p['event_grid']:
    step=2 if binary else 1;n=step*math.ceil(ev/eventp/step)
    power=cox_power(n,eventp,beta,sd,r2,p['alpha'],onesided);previous=cox_power(n-step,eventp,beta,sd,r2,p['alpha'],onesided)
    row={('hazard_ratio' if binary else 'r_squared'):a,'event_probability':eventp,'continuous_events':ev,'required_events':math.ceil(ev),'total_n':n,'achieved_power':power,'preceding_power':previous};rows.append(row)
    if a==(p['hazard_ratio'] if binary else p['r_squared']) and eventp==p['event_probability']:values={'event_requirement_continuous':ev,'required_events':math.ceil(ev),'sample_size':n,'achieved_power':power,'preceding_power':previous}
  details={'reference_is_asymptotic_approximation':True,'recruitment_rounding':'Ceil unrounded events / event probability; round even only for binary equal-allocation variant.','published_required_events':66 if binary else 78,'published_sample_size':66 if binary else 106,'published_locator':'Stata13 PDFp6 Example1 / PDFp9 adjusted Example4 (PDFpages count1-based)'}
 elif id=='wc26-open-cohort-sw':
  rows=[sw_row(p,g) for g in p['g_grid']];r=next(r for r in rows if r['clusters_per_sequence']==p['clusters_per_sequence'])
  values={k:r[k] for k in ['treatment_variance','mde','degrees_of_freedom','total_clusters']}
  _,V=sw_variance(p,p['clusters_per_sequence'])
  details={'covariance_matrix':V,'constant_pairwise_churn':True,'reference_is_t_quantile_mde_approximation':True,'published_mde':.269,'published_tolerance':.0005,'published_variance':.0085,'published_variance_tolerance':.00005,'published_locator':'NIH Worked Example open cohort discrete time Section2 PDFpp3–4'}
 else:raise ValueError(id)
 metrics=[row_result(m['metric'],values[m['metric']],m['unit'],m['integer']) for m in task['response_contract']['metrics']]
 integers={'n_per_arm','total_n','n_pairs','n_per_group','required_events','clusters_per_sequence','total_clusters','degrees_of_freedom'}
 coltol={k:0 if k in integers else 1e-8 if k=='treatment_variance' else 1e-6 if k in ['power','achieved_power','preceding_power','mde','rho','r_squared','event_probability','hazard_ratio'] else max(1e-6,max(abs(r[k]) for r in rows)*1e-6) for k in task['response_contract']['csv_columns']}
 return dict(id=id,kind='calculation',results=metrics,design={'method':task['response_contract']['method'],'alpha':p['alpha'],'alternative':task['response_contract']['alternative'],'allocation_ratio':p.get('allocation_ratio',1 if id.endswith('binary') else None),'sample_size_unit':task['response_contract']['sample_size_unit']},csv={'name':'sensitivity.csv','columns':task['response_contract']['csv_columns'],'key_columns':task['response_contract']['csv_key_columns'],'integer_columns':sorted(integers&set(task['response_contract']['csv_columns'])),'absolute_tolerances':coltol,'rows':rows},details=details,source_url=task['source_url'],requires_sources=True,requires_artifacts=True)
def main():
 tasks=json.loads((ROOT/'audited/tasks.json').read_text())['tasks'];out={'oracle_version':'workflow-capabilities-oracle1','python_version':sys.version.split()[0],'scipy_version':scipy.__version__,'numpy_version':np.__version__,'tasks':[oracle(t) for t in tasks]}
 path=ROOT/'audited/oracles.json';path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
 for o in out['tasks']:print(o['id'],[(r['metric'],r['value']) for r in o.get('results',[])])
if __name__=='__main__':main()
