args <- commandArgs(trailingOnly=TRUE)
root <- if (length(args)) args[1] else '.'
dat <- read.csv(file.path(root, 'results/publication-plot-data.csv'))
cols <- c(strict='#194D80', numerical_agreement='#D38528')
draw_tiers <- function() {
  par(mfrow=c(1,2), mar=c(4.4,4.8,3.2,1.2), oma=c(3,0,2,0))
  for (mode in c('single','multi')) {
    # R evaluates data-column names before local variables; select mode explicitly.
    d <- dat[dat$cohort=='linux40' & dat$mode==mode & dat$tier>0 & dat$metric %in% names(cols), ]
    plot(NA, xlim=c(.5,4.5), ylim=c(0,1.08), xaxt='n', xlab='Tier', ylab='All-planned agreement rate', main=paste('Linux:',mode))
    axis(1, at=1:4, labels=paste0(1:4, '\n(n=', c(6,6,4,4),')'))
    abline(h=seq(0,1,.25), col='#dddddd', lty=3)
    for (metric in names(cols)) {
      q <- d[d$metric==metric, ]; x <- q$tier + if(metric=='strict') -.11 else .11
      segments(x,q$lower95,x,q$upper95,col=cols[metric],lwd=2)
      points(x,q$rate,pch=if(metric=='strict')16 else 17,col=cols[metric],cex=1.2)
      text(x,q$rate+.035,labels=paste0(q$passed,'/',q$planned),col=cols[metric],cex=.78,pos=if(metric=='strict')2 else 4,offset=.2)
    }
  }
  mtext('Strict completion versus numerical-value agreement',outer=TRUE,side=3,line=.4,font=2)
  mtext('Numerical agreement includes incomplete responses. Bars: exploratory declared-family bootstrap 95% intervals.',outer=TRUE,side=1,line=.7,cex=.76)
  mtext('Only one attempt per task/mode; selected public tasks, no general-capability inference.',outer=TRUE,side=1,line=1.7,cex=.76)
  legend('topright',legend=c('Strict pipeline pass','Numerical value only'),col=cols,pch=c(16,17),bty='n',cex=.8)
}
pdf(file.path(root,'results/linux-strict-numeric.pdf'),width=10,height=5.8,useDingbats=FALSE)
draw_tiers();dev.off()
png(file.path(root,'results/linux-strict-numeric.png'),width=1600,height=928,res=160)
draw_tiers();dev.off()
draw_cohorts <- function() {
  names <- c(linux40='Linux 40',mac120='Mac 120 (15 lost)',original_extension24='Old ext. 24 (7 lost)',corrected_extension24='New ext. 24')
  d <- dat[dat$tier==0 & dat$metric %in% c('strict','numerical_agreement'),]
  labels <- unique(d$cohort)
  par(mfrow=c(1,2),mar=c(8.6,4.5,3,1),oma=c(3,0,0,0))
  for (mode in c('single','multi')) {
    plot(NA,xlim=c(.5,length(labels)+.5),ylim=c(0,1.08),xaxt='n',xlab='',ylab='All-planned agreement rate',main=mode)
    axis(1,at=seq_along(labels),labels=names[labels],las=2,cex.axis=.73)
    abline(h=seq(0,1,.25),col='#dddddd',lty=3)
    for(metric in c('strict','numerical_agreement')) {
      q <- d[d$mode==mode & d$metric==metric,];q <- q[match(labels,q$cohort),]
      x <- seq_along(labels)+if(metric=='strict')-.11 else .11
      segments(x,q$lower95,x,q$upper95,col=cols[metric],lwd=2)
      points(x,q$rate,pch=if(metric=='strict')16 else 17,col=cols[metric],cex=1.2)
      text(x,q$rate+.035,labels=paste0(q$passed,'/',q$planned),col=cols[metric],cex=.78,pos=if(metric=='strict')2 else 4,offset=.2)
    }
  }
  mtext('Cohorts remain separate. Capture losses count as operational failures; unknown model status/usage are never imputed.',outer=TRUE,side=1,line=.8,cex=.73)
  mtext('Bars: exploratory declared-family bootstrap 95%; related constructed variants assessed in separate merged-label sensitivity.',outer=TRUE,side=1,line=1.8,cex=.73)
}
pdf(file.path(root,'results/cohort-strict-numeric.pdf'),width=11,height=7,useDingbats=FALSE)
draw_cohorts();dev.off()
png(file.path(root,'results/cohort-strict-numeric.png'),width=1760,height=1120,res=160)
draw_cohorts();dev.off()
