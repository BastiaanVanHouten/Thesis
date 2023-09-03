library(tidyverse)
library(dplyr)

dir.create("gen/data-preparation/temp/", recursive = TRUE)

data_imdb_dataset <- read.delim("data/IMDB/basics.csv.gz", header = FALSE, stringsAsFactors = FALSE)


# Extract the first row as column names
column_names <- as.character(data_imdb_dataset[1, ])
data_imdb_dataset <- data_imdb_dataset[-1, ]  # Remove the first row

# Set the extracted names as column names
colnames(data_imdb_dataset) <- column_names

# only movies > 2000
data_imdb_dataset <- filter(data_imdb_dataset, titleType == "movie", startYear >= 1998, primaryTitle == originalTitle)

# select only title , tconst, startYear, runtimeminutes, genres
data_imdb_dataset <- select(data_imdb_dataset, tconst, primaryTitle, startYear, genres, runtimeMinutes)

filtered_data <- subset(data_imdb_dataset, tconst %in% us_production_movies_cleaned$imdb_id)


# save dataset
write_csv(filtered_data, paste0('gen/data-preparation/temp/', "dataset_imdb.csv"))







# save dataset
write_csv(merged_data, paste0('gen/data-preparation/temp/', "merged.csv"))
