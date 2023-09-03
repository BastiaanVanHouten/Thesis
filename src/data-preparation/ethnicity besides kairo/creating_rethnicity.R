library("readr")
library("tidyverse")
library("dplyr")
library("stringr")
library("rethnicity")

cast_movies_data <- read_csv("data/scraped/cast_movies_data.csv")



# Split full names into parts using stringr
cast_movies_data$first_name <- word(cast_movies_data$cast_name, 1)
cast_movies_data$last_name <- str_replace(cast_movies_data$cast_name, paste0("^", cast_movies_data$first_name, " "), "")

# Creating unique names with split
unique_names_dataset <- data.frame(unique_name = unique(cast_movies_data$cast_name))
unique_names_dataset$first_name <- word(unique_names_dataset$unique_name, 1)
unique_names_dataset$last_name <- str_replace(unique_names_dataset$unique_name, paste0("^", unique_names_dataset$first_name, " "), "")


# Extract first names and last names into separate vectors
first_names_vector <- unique_names_dataset$first_name
last_names_vector <- unique_names_dataset$last_name


# using rethncity to predict ethnicity
ethnicity_actors <- predict_ethnicity(firstnames = first_names_vector, lastnames = last_names_vector, method = "fullname")


# adding 
actors_with_ethnicity <- left_join(cast_movies_data, ethnicity_actors, by = c("first_name" = "firstname"  , "last_name" = "lastname"))


# Save the dataset
write_csv(actors_with_ethnicity, file.path("gen", "data-preparation", "temp", "actors_with_rethnicity.csv"))
