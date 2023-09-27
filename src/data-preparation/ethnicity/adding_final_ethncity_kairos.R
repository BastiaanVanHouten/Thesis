
library("readr")
library("tidyverse")
library("dplyr")
library("stringr")
library("rethnicity")

# List of ethnicity columns
ethnicity_columns <- c("asian", "black", "hispanic", "white", "age", "gender", "confidence")

# Loop through each ethnicity column and fill missing values
for (col in ethnicity_columns) {
  combined_data[[paste0(col, ".x")]] <- ifelse(
    is.na(combined_data[[paste0(col, ".x")]]),
    combined_data[[paste0(col, ".y")]],
    combined_data[[paste0(col, ".x")]]
  )
}

# Now, combined_data has missing values in .x columns filled with corresponding values from .y columns

# List of ethnicity columns with .y suffix
ethnicity_columns_y <- paste0(ethnicity_columns, ".y")

# Remove columns with .y suffix
combined_data <- combined_data %>%
  select(-one_of(ethnicity_columns_y))

write.csv(combined_data, "Master/Thesis/gen/data-preparation/output/the_final_ethncitiy_file.csv")


library(dplyr)


the_final_ethnicity_file <- the_final_ethnicity_file %>%
  select(-c("Movie ID", "Cast Member Name", "Profile Picture")) %>%
  distinct(actor_imdb_id, .keep_all = TRUE)


movie_cast_ethnicity <- left_join(movie_cast, the_final_ethnicity_file, by = "actor_imdb_id")

cast_movies_data <- movie_cast_ethnicity %>%
  filter(is.na(asian))



cast_movies_data <- read_csv("data/scraped/cast_movies_data.csv")


# Creating unique names with split
unique_names_dataset <- cast_movies_data %>%
  distinct(`Cast Member Name`, .keep_all = TRUE) %>%
  mutate(first_name = word(`Cast Member Name`, 1),
         last_name = str_replace(`Cast Member Name`, paste0("^", first_name, " "), "")
  )




# Extract first names and last names into separate vectors
first_names_vector <- unique_names_dataset$first_name
last_names_vector <- unique_names_dataset$last_name


# using rethncity to predict ethnicity
ethnicity_actors <- predict_ethnicity(firstnames = first_names_vector, lastnames = last_names_vector, method = "fullname")


# Combine first_name and last_name to create Cast Member Name
ethnicity_actors <- ethnicity_actors %>%
  mutate('Cast Member Name' = paste(firstname, lastname , sep = " "))


# adding 
actors_with_ethnicity <- left_join(movie_cast_ethnicity, ethnicity_actors, by = 'Cast Member Name') 

actors_with_ethnicity <- actors_with_ethnicity %>%
  select(-firstname, -lastname, -race)


# Assuming you have two data frames: actors_with_ethnicity and replacement_data
# Replace NA values in actors_with_ethnicity with values from replacement_data

# Define the ethnicity columns you want to replace
ethnicity_columns <- c("asian", "black", "hispanic", "white")

# Loop through each ethnicity column and fill missing values
for (col in ethnicity_columns) {
  actors_with_ethnicity[[col]] <- ifelse(
    is.na(actors_with_ethnicity[[col]]),
    actors_with_ethnicity[[paste0("prob_", col)]],
    actors_with_ethnicity[[col]]
  )
}


# Select all columns that do not start with "prob_" and remove firstname, lastname, and race columns
actors_with_ethnicity <- actors_with_ethnicity %>%
  select(-starts_with("prob_"), -firstname, -lastname, -race)


na_count <- sum(is.na(actors_with_ethnicity$asian))


# Save the dataset
write.csv(actors_with_ethnicity, file.path("Master/Thesis/gen/data-preparation/output/actors_with_ethnicity.csv"))
