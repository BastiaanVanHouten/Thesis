> movie_details_OMDB_1000 <- read_csv("data/scraped/movie_details_OMDB_1000.csv", 
                                      +     col_types = cols(`Rotten Tomatoes Value` = col_number(), 
                                                             +         `Metacritic Value` = col_number(), 
                                                             +         `IMDb Rating` = col_number(), `IMDb Votes` = col_number(), 
                                                             +         `Box Office` = col_number(), `Internet Movie Database` = col_number(), 
                                                             +         Metascore = col_number()))


library(purrr)
library(readr)
library(dplyr)

# List of file names
file_names <- c("movie_details_OMDB_1000.csv",
                "movie_details_OMDB_1000_2000.csv",
                "movie_details_OMDB_2000_3000.csv",
                "movie_details_OMDB_3000_4000.csv",
                "movie_details_OMDB_4000_5000.csv",
                "movie_details_OMDB_5000_6000.csv",
                "movie_details_OMDB_6000_7000.csv",
                "movie_details_OMDB_7000_8000.csv",
                "movie_details_OMDB_8000_8660.csv",
                "movie_details_OMDB_1000_1181.csv",
                "movie_details_OMDB_18_19.csv")

# Function to read CSV with specific column types
read_csv_with_types <- function(file_path) {
    read_csv(file_path, 
             col_types = cols(`Rotten Tomatoes Value` = col_number(), 
                              `Metacritic Value` = col_number(), 
                              `IMDb Rating` = col_number(), 
                              `IMDb Votes` = col_number(), 
                              `Box Office` = col_number(), 
                              `Internet Movie Database` = col_number(), 
                              Metascore = col_number()))
}

# Read and combine all CSV files with specific column types
combined_data <- map_dfr(file_names, ~ read_csv_with_types(paste("data/scraped/omdb_rankings/", .x, sep = "")))

head(combined_data)


# Remove the "Production" column
combined_data <- select(combined_data, -Production)


file_paths <- c("data/scraped/omdb_rankings/movie_details_OMDB_not_done_1000.csv", "data/scraped/omdb_rankings/movie_details_OMDB_not_done_1000_2000.csv", "data/scraped/omdb_rankings/movie_details_OMDB_not_done_2000_3000.csv", "data/scraped/omdb_rankings/movie_details_OMDB_not_done_3000_4000.csv", "data/scraped/omdb_rankings/movie_details_OMDB_not_done_4000_5000.csv", "data/scraped/omdb_rankings/movie_details_OMDB_not_done_5000_6000.csv", "data/scraped/omdb_rankings/movie_details_OMDB_not_done_6000_6023.csv")

# Read all CSV files into a list of data frames
list_of_data_frames <- lapply(file_paths, function(path) {
    read_csv(path)
})


# Combine the list of data frames into one data frame
combined_data_not_done <- do.call(rbind, list_of_data_frames)


# Create a list of data frames (replace these with your actual data frames)
awards_ratings <- rbind(combined_data, combined_data_not_done)



# Save the dataset
write_csv(awards_ratings, file.path("gen", "data-preparation", "temp", "awards_ratings.csv"))


