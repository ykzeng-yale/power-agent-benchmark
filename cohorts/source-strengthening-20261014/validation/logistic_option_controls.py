from pathlib import Path
import scipy,math,json
from scipy.integrate import quad
from scipy.special import expit,logit
from scipy.stats import norm
import sys
Q=Path(sys.argv[1]) if len(sys.argv)>1 else Path('reproduction-output');Q.mkdir(parents=True,exist_ok=True);rows=[]
for distribution,r2,alpha,target,onesided,bookN in [('normal',.1,.05,.85,True,51),('binary',.25,.05,.8,False,188)]:
 b0=logit(.1);b1=logit(.3)-b0
 if distribution=='normal':
  moments=[quad(lambda x,j=j:x**j*expit(b0+b1*x)*(1-expit(b0+b1*x))*norm.pdf(x),-12,12,epsabs=1e-12,epsrel=1e-12)[0] for j in range(3)]
  mu=quad(lambda x:expit(b0+b1*x)*norm.pdf(x),-12,12,epsabs=1e-12,epsrel=1e-12)[0];varx=1;a=1
 else:
  p=.6;moments=[(1-p)*(.1*.9)+(p*.3*.7),p*.3*.7,p*.3*.7];mu=.4*.1+.6*.3;varx=.6*.4;a=.85
 i0,i1,i2=moments;v1=i0/(i0*i2-i1*i1);v0=1/(varx*mu*(1-mu))
 for corrected in [False,True]:
  aa=a if corrected else 0;sd=math.sqrt((aa*v0+(1-aa)*v1)/v1);z=norm.ppf(1-alpha/(1 if onesided else 2))
  def pw(n):
   m=b1*math.sqrt(n*(1-r2)/v1)
   return norm.sf((z-m)/sd)+(norm.cdf((-z-m)/sd) if not onesided else 0)
  ns=next(n for n in range(1,10001) if pw(n)>=target)
  rows.append({'distribution':distribution,'variance_correction':corrected,'a':aa,'v1':v1,'v0':v0,'mean_event_probability':mu,'minimum_N':ns,'power_at_min':pw(ns),'power_at_predecessor':pw(ns-1),'book_N':bookN,'power_at_bookN':pw(bookN),'input_beta':b1,'r2_other_predictors':r2,'method':'GPower manual29.6.2 Demidenko eq14-15 with expected Fisher info','actual_reference_scope':'Large-sample corrected/uncorrected normal approximation, not finite-sample logistic fitting/simulation'})
with (Q/'independent-Python-Fisher-GPower-convention.json').open('x') as f:json.dump({'scipy_version':scipy.__version__,'source':'https://www.psychologie.hhu.de/fileadmin/redaktion/Fakultaeten/Mathematisch-Naturwissenschaftliche_Fakultaet/Psychologie/AAP/gpower/GPowerManual.pdf','printed_source_pages':[72,73],'rows':rows},f,indent=2);f.write('\n')
print(json.dumps(rows))
