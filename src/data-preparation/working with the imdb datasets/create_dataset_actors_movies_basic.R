library(tidyverse)

data_actors <- read.delim("data/IMDB/principals.csv.gz", header = FALSE, stringsAsFactors = FALSE)

# Set the first row as column names
column_names_actors <- as.character(data_actors[1, ])
data_actors <- data_actors[-1, ]  # Remove the first row
colnames(data_actors) <- column_names_actors


# Filter for only the movies in the main database and filter for actress, actor or director and remove the columm job
data_actors <- data_actors %>%
    filter(tconst %in% main_base$imdb_id)%>%
    filter(category %in% c("actress", "actor")) %>%
    select(-job)


# If changes to the dataset occured later use the following code instead of loading the entire datasetfile
data_actors <- read_csv("gen/data-preparation/temp/actors_movies_base.csv")
main_base <- read_csv("gen/data-preparation/temp/main_base.csv")

## make adjustments to the file


# save dataset
write_csv(data_actors, paste0('gen/data-preparation/temp/', "four_most_important_actors_imdb.csv"))
