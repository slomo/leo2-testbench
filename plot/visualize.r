#!/usr/bin/env Rscript
library(ggplot2)
options(width = 120)

filenames = commandArgs(trailingOnly = TRUE)

tptp <- read.csv("TPTP-v5.5.0/higherOrderStatus.csv", strip.white=TRUE, col.names=c("problem", "expected_status"))


categorize <- function(row) {
   if (row["status"] == "Timeout" || row["status"] == "Error") {
      return(row["status"])
   } else { if (row["status"] == row["expected_status"]) {
      return("Correct")
   } else {
      return("Incorrect")
   }}
}

for (filename in filenames) {

    filedata <- read.csv(file.path(filename,"summary.csv"),
                         strip.white=TRUE, header = TRUE)

    #runInfo <- read.csv(header=FALSE, check.names=FALSE, file.path(filename,"config.csv"))
    # subprovers <- print(paste(t(runInfo[,-(1:2)])[,1], collapse = " and "))
    # infoStr <- paste("Leo",runInfo[1,1],"using",subprovers)

    config <- paste(readLines(file.path(filename,"config.sh")), collapse =" ")
    leoVersion <- sub("^.*LEO_VERSION=\"?([a-z]*)-([a-z0-9\\.]*)\"?.*$","\\1 \\2",config)
    leoVersion <- sub("release ","", leoVersion)
    provers <- sub("^.*FO_PROVERS=\\(\\s*(.*?)\\s*\\).*$","\\1",config)
    provers <- gsub(" ",", ",provers)
    provers <- gsub("\"","", provers)
    provers <- gsub("-"," ", provers)
    numJobs <- sub(".*APPEND_OPTS=\".*?-aj (\\d+).*","\\1", config)
    if (nchar(numJobs) > 2 ) {
      infoStr <- paste0("leo ",leoVersion," (",provers,")");
    } else {
      infoStr <- paste0("leo ",leoVersion," (",provers,") parallel: ",numJobs);
    }


    filedata$configuration <- infoStr

    filedata <- merge(filedata, tptp, by="problem")
    filedata$category <- apply(filedata, MARGIN=1, FUN=categorize)

    if (exists("solutions")) {
      solutions <- rbind(solutions, filedata)
    } else {
      solutions <- filedata
    }
}


configurations <- c(unique(solutions['configuration']))


corSolutions <- subset(solutions, 1==1)
corSolutions <- ddply(solutions, .(problem), function (df) { data.frame("sucess"= c(paste(df['configuration'], collapse = " ")))  })
corSolutions

ggplot(solutions, aes(category,  fill=configuration )) +
geom_bar( position="dodge" )

#ggplot(corSolutions, aes(problem, fill=sucess)) +
#geom_bar( position="dodge" )

ggplot(corSolutions, mapping=aes(x="problem", y="realtime"), size=5) +
geom_jitter()
                      



                    
#ggplot(solutions, aes(problem, fill=category)) +
#geom_bar()


#geom_text(aes(label = category), size = 3, hjust = 0.5, vjust = 3, position ="")
#geom_boxplot() + coord_flip()

