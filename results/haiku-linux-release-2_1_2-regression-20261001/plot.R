args <- commandArgs(trailingOnly=TRUE)
folder <- if(length(args)) args[1] else '.'
dat <- read.csv(file.path(folder,'publication-plot-data.csv'))
cols <- c(strict='#194D80',numerical_agreement='#D38528')
draw <- function() {
  par(mfrow=c(1,2),mar=c(4.4,4.8,3.2,1.2),oma=c(3,0,2,0))
  for(mode in c('single','multi')) {
    d <- dat[dat$mode==mode & dat$tier>0 & dat$metric %in% names(cols),]
    plot(NA,xlim=c(.5,4.5),ylim=c(0,1.08),xaxt='n',xlab='Tier',
         ylab='All-planned agreement rate',main=paste('Release 2.1.2:',mode))
    axis(1,at=1:4,labels=paste0(1:4,'\n(n=',c(6,6,4,4),')'))
    abline(h=seq(0,1,.25),col='#dddddd',lty=3)
    for(metric in names(cols)) {
      q <- d[d$metric==metric,]; x <- q$tier+if(metric=='strict') -.11 else .11
      segments(x,q$lower95,x,q$upper95,col=cols[metric],lwd=2)
      points(x,q$rate,pch=if(metric=='strict')16 else 17,col=cols[metric],cex=1.2)
      text(x,q$rate+.035,labels=paste0(q$passed,'/',q$planned),
           col=cols[metric],cex=.78,pos=if(metric=='strict')2 else 4,offset=.2)
    }
    legend('topright',legend=c('Strict workflow pass','Numerical value only'),
           col=cols,pch=c(16,17),bty='n',cex=.76)
  }
  mtext('Frozen current-release regression: all 40 planned transports retained',outer=TRUE,side=3,line=.4,font=2)
  mtext('Numerical agreement includes unfinished responses. Bars: descriptive declared-family bootstrap 95% intervals.',
        outer=TRUE,side=1,line=.7,cex=.75)
  mtext('Selected developer-exposed tasks; one attempt per task/mode. No general-accuracy or cross-version causal claim.',
        outer=TRUE,side=1,line=1.7,cex=.75)
}
pdf(file.path(folder,'release-strict-numeric.pdf'),width=10,height=5.8,useDingbats=FALSE)
draw();dev.off()
png(file.path(folder,'release-strict-numeric.png'),width=1600,height=928,res=160)
draw();dev.off()
