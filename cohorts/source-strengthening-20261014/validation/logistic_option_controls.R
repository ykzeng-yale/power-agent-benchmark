args<-commandArgs(TRUE); output<-if(length(args))args[1] else 'reproduction-output/independent-R-Fisher-GPower-convention.json'
if(file.exists(output))stop('Refusing to overwrite an existing reproduction output')
dir.create(dirname(output),recursive=TRUE,showWarnings=FALSE)
# Independent expected-information option control; no simulation or model call.
rows <- list()
b0 <- qlogis(.1); b1 <- qlogis(.3)-b0
for (distribution in c('normal','binary')) {
 if (distribution=='normal') {
  moments <- sapply(0:2,function(j)integrate(function(x)x^j*plogis(b0+b1*x)*(1-plogis(b0+b1*x))*dnorm(x),-Inf,Inf,rel.tol=1e-12,abs.tol=1e-12,subdivisions=500)$value)
  mu <- integrate(function(x)plogis(b0+b1*x)*dnorm(x),-Inf,Inf,rel.tol=1e-12,abs.tol=1e-12,subdivisions=500)$value
  varx <- 1; a <- 1; r2 <- .1; target <- .85; sides <- 1; bookN <- 51
 } else {
  px <- .6; moments <- c((1-px)*.1*.9+px*.3*.7,px*.3*.7,px*.3*.7)
  mu <- (1-px)*.1+px*.3; varx <- px*(1-px); a <- .85; r2 <- .25; target <- .8; sides <- 2; bookN <- 188
 }
 v1 <- moments[1]/(moments[1]*moments[3]-moments[2]^2)
 v0 <- 1/(varx*mu*(1-mu))
 for (corrected in c(FALSE,TRUE)) {
  aa <- if(corrected)a else 0; sigma <- sqrt((aa*v0+(1-aa)*v1)/v1); z <- qnorm(1-.05/sides)
  pw <- function(n) {mean <- b1*sqrt(n*(1-r2)/v1);pnorm(z,mean,sigma,lower.tail=FALSE)+if(sides==2)pnorm(-z,mean,sigma)else 0}
  n <- (1:10000)[which(pw(1:10000)>=target)[1]]
  rows[[length(rows)+1]] <- list(distribution=distribution,variance_correction=corrected,v1=v1,v0=v0,mean_event_probability=mu,minimum_N=n,power_at_min=pw(n),power_at_predecessor=pw(n-1),book_N=bookN,power_at_bookN=pw(bookN))
 }
}
writeLines(jsonlite::toJSON(list(R=R.version.string,method='Independent R integrate / exact binary-information expression / normal tails from GPower manual29.6.2',rows=rows),pretty=TRUE,auto_unbox=TRUE,digits=15),output)
