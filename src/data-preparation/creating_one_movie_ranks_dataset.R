library(readr)
library(lubridate)

# Create a sequence of dates from '1998-02-03' to '2023-07-18'
start_date <- ymd('1998-02-03')
end_date <- ymd('2023-07-18')
date_sequence <- seq(start_date, end_date, by = '1 week')

# Convert the dates to character format with the desired format
new_column_names <- c("movie_id", format(date_sequence, format = "%Y-%m-%d"))

# reading 900 as numeric
# Read the CSV file while converting all columns except the first one to numeric
movie_ranks_900 <- read_csv(
    "data/scraped/movie_ranks_0_900.csv",
    col_types = cols(
        .default = col_number(),  # Set all non-first columns to numeric
        `movie_id` = col_character()  # Replace '1st_column_name' with the actual name of the first column
    )
)


# Read the CSV file while converting all columns except the first one to numeric
movie_ranks_900_3000 <- read_csv(
    "gen/data-preparation/temp/movie_ranks_900_3000.csv",
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


# Rename the columns
names(movie_ranks_900_3000) <- new_column_names





# reading 3000 -> 8660 as numeric
# Read the CSV file while converting all columns except the first one to numeric
movie_ranks_3000_8660 <- read_csv(
    "data/scraped/movie_ranks_3000_8660.csv",
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


# Rename the columns
names(movie_ranks_3000_8660) <- new_column_names



#combining all datasets
total_movie_ranks <- rbind(movie_ranks_900,movie_ranks_900_3000, movie_ranks_3000_8660 )


# Check for duplicates in the "movie_id" column
duplicates <- total_movie_ranks[duplicated(total_movie_ranks$movie_id), ]

# Show the rows with duplicate movie_ids
print(duplicates)

# Remove duplicates from the "movie_id" column
unique_movie_ranks <- total_movie_ranks[!duplicated(total_movie_ranks$movie_id), ]


# Save the dataset
write_csv(unique_movie_ranks, file.path("gen", "data-preparation", "output", "movie_ranks.csv"))
