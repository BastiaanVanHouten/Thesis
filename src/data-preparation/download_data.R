## Load libraries
library(tidyverse)
library(dplyr)

dir.create("data")

## Load the URLs
options(timeout = max(1000, getOption("timeout")))

urls <- c("https://datasets.imdbws.com/title.basics.tsv.gz")

## Names for each URL
names <- c("basics", "language")

for (i in 1:length(urls)) {
    download.file(urls[i], paste0('data/', names[i], ".csv.gz"), mode = "wb")
}
