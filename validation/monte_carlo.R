#!/usr/bin/env Rscript
# Constructed calibration experiment, not a textbook or LLM-evaluation task.
# Raw repeated outcomes are generated from a Gaussian random-intercept DGP.
args <- commandArgs(TRUE)
root <- if(length(args)) args[1] else "."
protocol <- jsonlite::fromJSON(file.path(root,"validation/monte-carlo-protocol.json"),simplifyVector=FALSE)
wilson <- function(k,B) {
  z <- qnorm(.975); p <- k/B; den <- 1+z*z/B
  center <- (p+z*z/(2*B))/den
  half <- z*sqrt(p*(1-p)/B+z*z/(4*B*B))/den
  c(center-half,center+half)
}
records <- list()
for(case in protocol$cases) for(seed in unlist(protocol$seeds)) {
  set.seed(seed)
  B <- protocol$trials; n <- case$n_per_arm; m <- case$measurements
  # Each row is one trial. Each participant's intercept is shared across m outcomes.
  subject_mean <- matrix(rnorm(B*2*n,sd=case$tau),B,2*n)
  for(j in seq_len(m)) subject_mean <- subject_mean+matrix(rnorm(B*2*n,sd=case$sigma/m),B,2*n)
  treatment <- subject_mean[,seq_len(n),drop=FALSE]+case$mean_difference
  control <- subject_mean[,n+seq_len(n),drop=FALSE]
  mt <- rowMeans(treatment); mc <- rowMeans(control)
  vt <- (rowSums(treatment^2)-n*mt^2)/(n-1)
  vc <- (rowSums(control^2)-n*mc^2)/(n-1)
  statistic <- (mt-mc)/sqrt((vt+vc)/n)
  critical <- qt(1-case$alpha/2,2*n-2)
  failed <- sum(!is.finite(statistic))
  rejected <- sum(is.finite(statistic)&abs(statistic)>critical)
  power <- rejected/B
  variance_of_subject_mean <- case$tau^2+case$sigma^2/m
  nc <- case$mean_difference*sqrt(n/(2*variance_of_subject_mean))
  exact <- pt(critical,2*n-2,ncp=nc,lower.tail=FALSE)+pt(-critical,2*n-2,ncp=nc)
  records[[length(records)+1]] <- list(
    case_id=case$id,seed=seed,trials=B,rejections=rejected,
    nonrejections=B-rejected-failed,failures=failed,
    method=protocol$method,parameters=case,
    estimate=power,mcse=sqrt(power*(1-power)/B),wilson_95=wilson(rejected,B),
    analytic_power=exact,R=R.version.string)
}
result <- list(kind="Constructed Monte Carlo calibration, no model evaluation",records=records)
writeLines(jsonlite::toJSON(result,pretty=TRUE,auto_unbox=TRUE,digits=15),file.path(root,"validation/monte-carlo-results.json"))
cat("Saved",length(records),"independently seeded simulations\n")
