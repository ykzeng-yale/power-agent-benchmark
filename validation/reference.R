#!/usr/bin/env Rscript
# Canonical R oracle. Integer designs are solved on their feasible allocation grid.
args<-commandArgs(TRUE); root<-if(length(args))args[1] else '.'
specs<-jsonlite::fromJSON(file.path(root,'audited/reference-specifications.json'),simplifyVector=FALSE)
tasks<-jsonlite::fromJSON(file.path(root,'audited/tasks.json'),simplifyVector=FALSE)$tasks
first_integer<-function(fn,target,start=2){for(n in seq.int(start,100000)){if(fn(n)>=target)return(n)};stop('No feasible sample size')}
power_t<-function(n,d,alpha,alternative,two){df<-if(two)2*n-2 else n-1;nc<-d*sqrt(if(two)n/2 else n);sides<-if(alternative=='two_sided')2 else 1;critical<-qt(1-alpha/sides,df);pt(critical,df,ncp=nc,lower.tail=FALSE)+if(sides==2)pt(-critical,df,ncp=nc)else 0}
noncentral_f<-function(N,u,v,f2,alpha){pf(qf(1-alpha,u,v),u,v,ncp=N*f2,lower.tail=FALSE)}
riley<-function(method,p){q<-p$parameters;r<-p$rsquared;s<-p$shrinkage
 if(method=='riley_continuous'){
  shrink<-function(n)1+(q-2)/(n*log(1-(r*(n-q-1)+q)/(n-1)))
  n1<-first_integer(shrink,s,start=q+2);n2<-ceiling(1+q*(1-r)/p$rsquared_difference);sd_mmoe<-function(n){df<-n-q-1;sqrt(max(qchisq(.975,df)/df,df/qchisq(.025,df)))};n3<-first_integer(function(n)-sd_mmoe(n),-p$residual_sd_mmoe,start=q+2);n4<-max(n1,n2,n3)
  while(qt(.975,n4-q-1)*sqrt(p$sd^2*(1-r)/n4)>abs(p$intercept)*(p$intercept_mmoe-1))n4<-n4+1
  return(list(value=max(n1,n2,n3,n4),criteria=c(n1,n2,n3,n4)))
 }
 n1<-ceiling(q/((s-1)*log1p(-r/s)))
 maxr<-if(method=='riley_binary')1-exp(2*(p$prevalence*log(p$prevalence)+(1-p$prevalence)*log1p(-p$prevalence)))else{e<-ceiling(p$rate*p$meanfup*10000);1-exp(2*(e*log(e/10000)-e)/10000)}
 s2<-r/(r+p$rsquared_difference*maxr);n2<-ceiling(q/((s2-1)*log1p(-r/s2)))
 n3<-if(method=='riley_binary')ceiling((1.96/p$risk_halfwidth)^2*p$prevalence*(1-p$prevalence))else first_integer(function(n){risk<-1-exp(-p$rate*p$timepoint);se<-sqrt(p$rate/(p$meanfup*n));upper<-1-exp(-(p$rate+1.96*se)*p$timepoint); -(upper-risk)},-p$risk_halfwidth,start=2)
 list(value=max(n1,n2,n3),criteria=c(n1,n2,n3))
}
rows<-lapply(seq_along(specs),function(i){s<-specs[[i]];p<-s$parameters;m<-s$method;alpha<-if(is.null(p$alpha)).05 else p$alpha;alt<-s$expected_design$alternative;criteria<-NULL;package_value<-NULL
 if(startsWith(m,'riley')){result<-riley(m,p);value<-result$value;criteria<-result$criteria;pkg<-do.call(pmsampsize::pmsampsize,c(list(type=switch(m,riley_binary='b',riley_survival='s',riley_continuous='c')),p[intersect(names(p),c('parameters','prevalence','rate','meanfup','timepoint','shrinkage','intercept','sd','mmoe'))],setNames(list(p$rsquared),if(m=='riley_continuous')'rsquared'else 'csrsquared')));package_value<-pkg$sample_size
 }else if(m=='proportion_precision'){value<-ceiling(qnorm(1-alpha/2)^2*p$p*(1-p$p)/p$margin^2)
 }else{
  if(m%in%c('one_sample_t','two_sample_t','paired_t'))fn<-function(n)power_t(n,p$d,alpha,alt,m=='two_sample_t')
  if(m=='linear_regression')fn<-function(n)noncentral_f(n,p$u,n-p$p-1,p$f2,alpha)
  if(m=='one_way_anova')fn<-function(n){N<-if(s$metric=='power')n else n*p$groups;noncentral_f(N,p$groups-1,N-p$groups,p$f2,alpha)}
  if(m=='factorial_anova')fn<-function(n)noncentral_f(n*p$cells,p$u,n*p$cells-p$cells,p$f2,alpha)
  if(m=='rm_between')fn<-function(n)noncentral_f(n*2,1,n*2-2,p$f2*p$measurements/(1+(p$measurements-1)*p$rho),alpha)
  if(m=='rm_within')fn<-function(n)noncentral_f(n,(p$measurements-1)*p$epsilon,(n-1)*(p$measurements-1)*p$epsilon,p$f2*p$measurements/(1-p$rho)*p$epsilon,alpha)
  if(m=='rm_interaction')fn<-function(n)noncentral_f(2*n,(p$measurements-1)*p$epsilon,(2*n-2)*(p$measurements-1)*p$epsilon,p$f2*p$measurements/(1-p$rho)*p$epsilon,alpha)
  value<-if(s$metric=='power')fn(p$n)else first_integer(fn,p$power,start=if(m=='linear_regression')p$p+2 else 2)
 }
 source<-s$published_source_value
 list(id=s$id,metric=s$metric,unit=s$unit,value=value,absolute_tolerance=s$absolute_tolerance,design=s$expected_design,source_value=source,source_difference=if(is.null(source))NULL else value-source,criteria=criteria,package_value=package_value,package_match=if(is.null(package_value))NULL else package_value==value)
})
result<-list(R=R.version.string,packages=list(pwr=as.character(packageVersion('pwr')),pmsampsize=as.character(packageVersion('pmsampsize')),jsonlite=as.character(packageVersion('jsonlite'))),tasks=rows)
writeLines(jsonlite::toJSON(result,pretty=TRUE,auto_unbox=TRUE,null='null',digits=15),file.path(root,'audited/oracles.json'))
cat('Verified ',length(rows),' R reference calculations\n');print(data.frame(id=sapply(rows,`[[`,'id'),value=sapply(rows,`[[`,'value'),source_difference=sapply(rows,function(x)if(is.null(x$source_difference))NA else x$source_difference)))
