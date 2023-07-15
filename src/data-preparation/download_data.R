## Load libraries
library(tidyverse)

dir.create("data")

## Load the URLs
options(timeout = max(1000, getOption("timeout")))

urls <- c("https://datasets.imdbws.com/title.basics.tsv.gz", 
          "https://datasets.imdbws.com/title.crew.tsv.gz",
          "https://datasets.imdbws.com/title.principals.tsv.gz",
          "https://datasets.imdbws.com/name.basics.tsv.gz")

## Names for each URL
names <- c("basics", "director", "principals", "name.basics")

for (i in 1:length(urls)) {
    download.file(urls[i], paste0('data/', names[i], ".csv.gz"), mode = "wb")
}

# Download zip from kaggle #
url <- "https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset/download?datasetVersionNumber=7"
file_name <- "archive.zip"

# Download the zip file
download.file(url, destfile = file_name, mode = "wb")

