#!/usr/bin/env Rscript
# Independent base-R implementation of the source-extension normal approximations.
args <- commandArgs(TRUE)
root <- if(length(args)) args[1] else "."
specs <- jsonlite::fromJSON(file.path(root,"audited/reference-specifications.json"),simplifyVector=FALSE)
rows <- lapply(specs,function(s) {
  p <- s$parameters
  if(s$method=="logrank_freedman") {
    if(s$metric=="power") {
      expected_events <- p$n * (p$pE+p$pC)
      value <- pnorm(sqrt(expected_events)*abs(p$HR-1)/(p$HR+1)-qnorm(.975))
    } else {
      required_events <- (qnorm(.975)+qnorm(p$power))^2 * (p$HR+1)^2/(p$HR-1)^2
      value <- ceiling(required_events/(p$pE+p$pC))
    }
  } else if(s$method=="cluster_rate_cv") {
    rate_variance <- (p$r1+p$r2)/p$exposure + p$cv^2*(p$r1^2+p$r2^2)
    value <- ceiling(1+(qnorm(.975)+qnorm(p$power))^2*rate_variance/(p$r1-p$r2)^2)
  } else stop("Unknown specified method")
  list(id=s$id,metric=s$metric,unit=s$unit,value=value,
       absolute_tolerance=s$absolute_tolerance,design=s$expected_design)
})
result <- list(implementation="Independent base R normal-approximation formulas",R=R.version.string,tasks=rows)
writeLines(jsonlite::toJSON(result,pretty=TRUE,auto_unbox=TRUE,digits=15),file.path(root,"audited/oracles.json"))
print(data.frame(id=sapply(rows,`[[`,"id"),value=sapply(rows,`[[`,"value")))
