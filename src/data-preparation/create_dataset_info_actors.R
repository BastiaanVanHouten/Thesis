library(tidyverse)

# Read the contents of the gz file
name_actors<- read.delim("data/IMDB/name.basics.csv.gz", header = FALSE, stringsAsFactors = FALSE)

# Extract the first row as column names
column_names_names_actors <- as.character(name_actors[1, ])

# Load the CSV file
actors_movies <- read.csv("gen/data-preparation/temp/actors_movies_base.csv")

# Subset the name_actors dataset using values from the CSV file
name_actors <- subset(name_actors, V1 %in% actors_movies$nconst)

# Set the extracted names as column names
colnames(name_actors) <- column_names_names_actors

# save dataset
write_csv(name_actors, paste0('gen/data-preparation/temp/', "info_actors.csv"))


