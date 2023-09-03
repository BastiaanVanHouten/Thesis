library(readr)
library(tidyr)
library(dplyr)

movie_ranks_900_1600 <- read_csv("data/scraped/movie_ranks/movie_ranks_900_1600.csv")
movie_ranks_1600_2300 <- read_csv("data/scraped/movie_ranks/movie_ranks_1600_2300.csv")
movie_ranks_2300_3000 <- read_csv("data/scraped/movie_ranks//movie_ranks_2300_3000.csv")
movie_ranks_900_3000_1998_ <- read_csv("data/scraped/movie_ranks/movie_ranks_900_3000_1998-.csv")

## combining 900 till 3000 
movie_ranks_900_2300 <- rbind(movie_ranks_900_1600, movie_ranks_1600_2300)

## adding 1998 -> 
movie_ranks_900_2300_complete <- inner_join(movie_ranks_900_3000_1998_, movie_ranks_900_2300)
movie_ranks_2300_3000_complete <- inner_join(movie_ranks_900_3000_1998_, movie_ranks_2300_3000, by= "movie_id")


# Get the column names from movie_ranks_2300_3000
cols_to_keep <- colnames(movie_ranks_2300_3000_complete)

# Subset movie_ranks_900_2300_subset to keep only the columns present in movie_ranks_2300_3000_complete
movie_ranks_900_2300_subset <- movie_ranks_900_2300_complete[, cols_to_keep]

# combining 900 - 3000
movie_ranks_900_3000 <- rbind(movie_ranks_900_2300_subset,movie_ranks_2300_3000_complete)


write_csv(movie_ranks_900_3000, "gen/data-preparation/temp/movie_ranks_900_3000.csv")
