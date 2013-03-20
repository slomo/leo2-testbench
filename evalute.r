#!/usr/bin/env Rscript
# -*- mode: R =*-

args <- commandArgs(TRUE)

loadData <- function(path){
         csvfile <- paste(path,"data.cvs",sep="/")
         data <- read.csv(file=csvfile, head=TRUE)
         return(data)
}

if (args[1] == "compare"){
   data1 <- loadData(args[2])
   data2 <- loadData(args[3])

   attach(data1)
   sucess1 <- data1[result == expectedResult ]   
   detach(data1)

   attach(data2)
   sucess2 <- data2[result == expectedResult ]   
   detach(data2)

   # compute counts of szs values
   counts <- rbind( table(sucess1$result), table(sucess2$result))



   # compute times   
   tmp <- merge(sucess1, sucess2, by=c("problem"), all=FALSE)
   runtimes <- subset(tmp, select=c("problem", "usertime.x", "usertime.y"))

   runtimes <- matrix( c(runtimes$usertime.x, runtimes$usertime.y) ,
            ncol= length(runtimes$problem),
            dimnames=list(
                runtimes$problem,
                list(
                        paste("times for", args[2]),
                        paste("times for", args[3])
                )
            )

   )
   runtimes <- t(runtimes)

   par(mfrow=c(1,2))
   
   barplot(counts,
        main="Comparrison of correct SZS-Stati",
        legend=c(args[2], args[3]),
        col=c("red","yellow"),
        beside=TRUE,
        horiz=TRUE
   )

   barplot(runtimes,
        main="Comparrison of per Problem runtime",
        beside=TRUE,
        horiz=TRUE,
        legend=rownames(runtimes)
   )

}

