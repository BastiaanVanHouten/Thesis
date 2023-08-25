
# Assuming your dataset is named cast_movies_data
# Split full names into parts
name_parts <- strsplit(cast_movies_data$cast_name, " ")

# Extract first and last names
cast_movies_data$first_name <- sapply(name_parts, "[", 1)
cast_movies_data$last_name <- sapply(name_parts, "[", length)

# Print the modified dataset
print(cast_movies_data)


# Load the stringr package
library(stringr)

# Assuming your dataset is named cast_movies_data
# Split full names into parts using stringr
cast_movies_data$first_name <- word(cast_movies_data$cast_name, 1)
cast_movies_data$last_name <- str_replace(cast_movies_data$cast_name, paste0("^", cast_movies_data$first_name, " "), "")

# Print the modified dataset
print(cast_movies_data)


# Assuming your dataset is named cast_movies_data
# Count the number of unique names in the cast_name column
unique_names_count <- length(unique(cast_movies_data$cast_name))

# Print the count of unique names
print(unique_names_count)


unique_names_dataset <- data.frame(unique_name = unique(cast_movies_data$cast_name))



# Extract first names and last names into separate vectors
first_names_vector <- cast_movies_data$first_name
last_names_vector <- cast_movies_data$last_name

ethnicity_actors <- predict_ethnicity(firstnames = first_names_vector, lastnames = last_names_vector, method = "fullname")


# Assuming your dataframe is named ethnicity_actors
write.csv(ethnicity_actors, file = "ethnicity_actors.csv", row.names = FALSE)


count_high_prob <- ethnicity_actors %>%
    filter(prob_asian > 0.75 | prob_black > 0.75 | prob_hispanic > 0.75 | prob_white > 0.75) %>%
    nrow()


unique_ethnicity_actors <- distinct(ethnicity_actors, firstname, lastname, .keep_all = TRUE)



actors_with_ethnicity <- left_join(cast_movies_data, unique_ethnicity_actors, by = c("first_name" = "firstname"  , "last_name" = "lastname"))


# Assuming your dataframe is named ethnicity_actors
write.csv(ethnicity_actors, file = "ethnicity_actors.csv", row.names = FALSE)

# Save the dataset
write_csv(actors_with_ethnicity, file.path("gen", "data-preparation", "output", "actors_with_ethnicity.csv"))
