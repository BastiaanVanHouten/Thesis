library(readr)
library(lubridate)

# reading 900 as numeric
# Read the CSV file while converting all columns except the first one to numeric
movie_ranks_900 <- read_csv(
    "movie_ranks_0_900.csv",
    col_types = cols(
        .default = col_number(),  # Set all non-first columns to numeric
        `movie_id` = col_character()  # Replace '1st_column_name' with the actual name of the first column
    )
)


# Read the CSV file while converting all columns except the first one to numeric
movie_ranks_900_3000 <- read_csv(
    "movie_ranks_900_3000.csv",
    col_types = cols(
        .default = col_number(),  # Set all non-first columns to numeric
        `movie_id` = col_character()  # Replace '1st_column_name' with the actual name of the first column
    )
)


# removing extra columms because of wrong numbering
# List of column indices to remove (1-based index)
columns_to_remove <- c(2, 3, 4, 5, 6)

# Remove the specified columns
movie_ranks_900_3000 <- movie_ranks_900_3000 %>%
    select(-columns_to_remove)

# Save the modified dataset if needed
write.csv(movie_ranks_900_3000, file = 'modified_dataset_2.csv', row.names = FALSE)

# Create a sequence of dates from '1998-02-03' to '2023-07-18'
start_date <- ymd('1998-02-03')
end_date <- ymd('2023-07-18')
date_sequence <- seq(start_date, end_date, by = '1 week')

# Convert the dates to character format with the desired format
new_column_names <- c("movie_id", format(date_sequence, format = "%Y-%m-%d"))

# Load your dataset
dataset_2 <- read.csv('modified_dataset_2.csv')

# Rename the columns
names(dataset_2) <- new_column_names


# reading 3000 -> 8660 as numeric


# Read the CSV file while converting all columns except the first one to numeric
movie_ranks_3000_8660 <- read_csv(
    "merged_movie_ranks_3000_8660.csv",
    col_types = cols(
        .default = col_number(),  # Set all non-first columns to numeric
        `movie_id` = col_character()  # Replace '1st_column_name' with the actual name of the first column
    )
)


# removing extra columms because of wrong numbering
# List of column indices to remove (1-based index)
columns_to_remove <- c(2, 3, 4, 5)

# Remove the specified columns
movie_ranks_3000_8660 <- movie_ranks_3000_8660 %>%
    select(-columns_to_remove)

# Save the modified dataset if needed
write.csv(dataset, file = 'modified_dataset.csv', row.names = FALSE)


# Create a sequence of dates from '1998-02-03' to '2023-07-18'
start_date <- ymd('1998-02-03')
end_date <- ymd('2023-07-18')
date_sequence <- seq(start_date, end_date, by = '1 week')

# Convert the dates to character format with the desired format
new_column_names <- c("movie_id", format(date_sequence, format = "%Y-%m-%d"))

# Load your dataset
dataset <- read.csv('modified_dataset.csv')

# Rename the columns
names(dataset) <- new_column_names

# Save the modified dataset if needed
write.csv(dataset, file = 'modified_dataset.csv', row.names = FALSE)


# Save the modified dataset if needed
write.csv(movie_ranks_3000_8660, file = 'modified_dataset.csv', row.names = FALSE)

#combining all datasets
total_movie_ranks <- rbind(movie_ranks_900,dataset_2, dataset )


# Save the dataset
write_csv(us_production_movies_cleaned, file.path("gen", "data-preparation", "output", "movie_ranks.csv"))
