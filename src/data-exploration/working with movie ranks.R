library(readr)

movie_ranks <- read_csv("gen/data-preparation/output/movie_ranks.csv",
                        col_types = cols(
                            .default = col_number(),  # Set all non-first columns to numeric
                            `movie_id` = col_character()  # Replace '1st_column_name' with the actual name of the first column
                        ))



# Save the movie_ranks_long dataframe as a CSV file
write.csv(movie_ranks_long, "movie_ranks_long.csv", row.names = FALSE)


# Replace all NA values in the movie_ranks dataset with 0
movie_ranks <- replace(movie_ranks, is.na(movie_ranks), 0)

movie_ranks_long <- movie_ranks_long %>%
    mutate(date = as.Date(date))



# Replace non-standard characters with valid ones for column names
colnames(movie_ranks) <- make.names(colnames(movie_ranks))




# Pivot and mutate the date column
movie_ranks_long <- movie_ranks %>%
    pivot_longer(cols = -movie_id, names_to = "date", values_to = "rank") %>%
    mutate(date = as.Date(date, format = "%Y.%m.%d"))


movie_ranks_long <- movie_ranks %>%
    pivot_longer(cols = -movie_id, names_to = "date", values_to = "rank") %>%
    mutate(date = as.Date(date))






library(tidyverse)

# Assuming your dataset is named 'movie_ranks'
movie_ranks_long <- movie_ranks %>%
    pivot_longer(cols = -movie_id, names_to = "date", values_to = "rank") %>%
    mutate(date = as.Date(date))

