# Evaluator-only reference, independently implemented with R base functions.
# No task answer/code from this file is sent to any agent.
args <- commandArgs(trailingOnly=TRUE)
root <- if(length(args)) args[[1]] else "cohorts/workflow-capabilities-20261002"
tasks <- jsonlite::fromJSON(file.path(root,"audited/tasks.json"),simplifyVector=FALSE)$tasks
minimum <- function(fn,target,step=1) { for(n in seq(2,100000,by=step)) if(fn(n)>=target) return(n); stop("Bound exceeded") }
tpower <- function(n,d,alpha,paired=FALSE) stats::power.t.test(n=n,delta=d,sd=1,sig.level=alpha,type=if(paired) "paired" else "two.sample",alternative="two.sided",strict=TRUE)$power
coxevent <- function(beta,sd,r2,alpha,power,one) (qnorm(1-alpha/if(one)1 else 2)+qnorm(power))^2/(beta^2*sd^2*(1-r2))
coxpower <- function(n,p,beta,sd,r2,alpha,one) pnorm(abs(beta)*sd*sqrt(n*p*(1-r2))-qnorm(1-alpha/if(one)1 else 2))
results <- list()
for(task in tasks) {
 p <- task$parameters; id <- task$id; rows <- list(); values <- list(); diagnostic <- list()
 if(task$outcome_kind=="clarification") next
 if(id=="wc26-pooled-t") {
  fn <- function(n) tpower(n,p$d,p$alpha)
  n <- minimum(fn,p$target_power)
  values <- list(sample_size=n,total_sample_size=2*n,achieved_power=fn(n),preceding_power=fn(n-1))
  rows <- lapply(p$grid_n,function(k)list(n_per_arm=k,total_n=2*k,power=fn(k)))
  diagnostic$continuous_n <- stats::power.t.test(delta=p$d,sd=1,sig.level=p$alpha,power=p$target_power,type="two.sample",alternative="two.sided",strict=TRUE,tol=1e-10)$n
 } else if(id=="wc26-paired-t") {
  for(rho in unlist(p$rho_grid)) {
   sd <- sqrt(2*p$measurement_sd^2-2*rho*p$measurement_sd^2)
   fn <- function(n) tpower(n,p$mean_difference/sd,p$alpha,TRUE)
   n <- minimum(fn,p$target_power)
   rows[[length(rows)+1]] <- list(rho=rho,difference_sd=sd,n_pairs=n,achieved_power=fn(n),preceding_power=fn(n-1))
   if(rho==p$rho) values <- list(sample_size=n,difference_sd=sd,achieved_power=fn(n),preceding_power=fn(n-1))
  }
 } else if(id=="wc26-anova") {
  means <- unlist(p$group_means)
  fn <- function(n) stats::power.anova.test(groups=p$groups,n=n,between.var=var(means),within.var=p$within_variance,sig.level=p$alpha)$power
  n <- minimum(fn,p$target_power)
  values <- list(sample_size=n,total_sample_size=p$groups*n,achieved_power=fn(n),preceding_power=fn(n-1))
  rows <- lapply(p$grid_n,function(k)list(n_per_group=k,total_n=p$groups*k,power=fn(k)))
  diagnostic$continuous_n <- stats::power.anova.test(groups=p$groups,between.var=var(means),within.var=p$within_variance,sig.level=p$alpha,power=p$target_power)$n
 } else if(id %in% c("wc26-cox-binary","wc26-cox-continuous")) {
  binary <- id=="wc26-cox-binary"; one <- !binary; sd <- if(binary) .5 else p$covariate_sd
  av <- if(binary) unlist(p$hr_grid) else unlist(p$r2_grid)
  for(a in av) {
   beta <- if(binary) log(a) else p$beta; r2 <- if(binary)0 else a
   event <- coxevent(beta,sd,r2,p$alpha,p$target_power,one)
   for(ep in unlist(p$event_grid)) {
    step <- if(binary)2 else 1; n <- step*ceiling(event/ep/step)
    row <- list(event_probability=ep,continuous_events=event,required_events=ceiling(event),total_n=n,achieved_power=coxpower(n,ep,beta,sd,r2,p$alpha,one),preceding_power=coxpower(n-step,ep,beta,sd,r2,p$alpha,one))
    row[[if(binary)"hazard_ratio" else "r_squared"]] <- a;rows[[length(rows)+1]]<-row
    if(a==if(binary)p$hazard_ratio else p$r_squared) if(ep==p$event_probability) values <- list(event_requirement_continuous=event,required_events=ceiling(event),sample_size=n,achieved_power=row$achieved_power,preceding_power=row$preceding_power)
   }
  }
 } else if(id=="wc26-open-cohort-sw") {
  # This differs from the Python projected-information scalar expression:
  # assemble full period-fixed-effects plus treatment GLS normal equations,
  # summing all g copies of each cluster sequence, then invert the whole matrix.
  sg <- p$icc*p$variance*(1-p$group_r_squared)
  sm <- (1-p$icc)*p$variance*(1-p$member_r_squared)/p$members_per_cluster_period
  V <- matrix(0,p$periods,p$periods)
  for(i in 1:p$periods)for(j in 1:p$periods) V[i,j]<-if(i==j)sg+sm else sg*p$cac^abs(i-j)+(1-p$pairwise_churn)*sm*p$iac^abs(i-j)
  chol(V);W<-solve(V)
  for(g in unlist(p$g_grid)) {
   info <- matrix(0,p$periods+1,p$periods+1)
   for(x in p$treatment_sequences) {Z<-cbind(diag(p$periods),unlist(x));info<-info+g*crossprod(Z,W%*%Z)}
   var <- solve(info)[p$periods+1,p$periods+1]
   df <- g*p$sequences-p$periods-1-p$group_covariate_df
   mde <- sqrt(var)*(qt(1-p$alpha/2,df)+qt(p$target_power,df))
   rows[[length(rows)+1]]<-list(clusters_per_sequence=g,total_clusters=g*p$sequences,degrees_of_freedom=df,treatment_variance=var,mde=mde)
   if(g==p$clusters_per_sequence) values<-list(treatment_variance=var,mde=mde,degrees_of_freedom=df,total_clusters=g*p$sequences)
  }
  diagnostic$covariance_matrix<-lapply(seq_len(nrow(V)),function(i)as.list(V[i,]))
 }
 results[[length(results)+1]]<-list(id=id,values=values,rows=rows,diagnostic=diagnostic)
}
out<-list(runtime=list(R=R.version.string,jsonlite=as.character(packageVersion("jsonlite"))),tasks=results)
writeLines(jsonlite::toJSON(out,auto_unbox=TRUE,digits=15,pretty=TRUE),file.path(root,"validation/r-reference.json"))
