library(tidyverse)
library(dplyr)

dir.create("gen/data-preparation/temp/", recursive = TRUE)

data <- read.delim("data/basics.csv.gz", header = FALSE, stringsAsFactors = FALSE)

# Extract the first row as column names
column_names <- as.character(data[1, ])
data <- data[-1, ]  # Remove the first row

# Set the extracted names as column names
colnames(data) <- column_names

# only movies > 2000
data <- filter(data, titleType == "movie", startYear >= 2000, primaryTitle == originalTitle)

# select only title , tconst, startYear, runtimeminutes, genres
data <- select(data, tconst, primaryTitle, startYear, genres, runtimeMinutes)


# save dataset
write_csv(data, paste0('gen/data-preparation/temp/', "basics.csv"))

