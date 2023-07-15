library(tidyverse)


## for directors ## 
data_directors <- read.delim("data/director.csv.gz", header = FALSE, stringsAsFactors = FALSE)

# Extract the first row as column names
column_names <- as.character(data_directors[1, ])
data_directors <- data_directors[-1, ]  # Remove the first row

# Set the extracted names as column names
colnames(data_directors) <- column_names

filtered_directors <- subset(data_directors, tconst %in% us_production_movies_cleaned$imdb_id)

# save dataset
write_csv(filtered_directors, paste0('gen/data-preparation/temp/', "directors.csv"))
