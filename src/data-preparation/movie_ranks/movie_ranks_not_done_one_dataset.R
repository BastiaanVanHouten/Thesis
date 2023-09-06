library(readr)
library(dplyr)

movie_ranks_not_done_2000 <- read_csv("movie_ranks_not_done_2000.csv")
movie_ranks_not_done_2000_4000 <- read_csv("movie_ranks_not_done_2000_4000.csv")
movie_ranks_not_done_4000_6023 <- read_csv("movie_ranks_not_done_4000_6023.csv")

movie_ranks_not_done_complete <- rbind(movie_ranks_not_done_2000,movie_ranks_not_done_2000_4000, movie_ranks_not_done_4000_6023)


unique_movie_ids_count <- movie_ranks_not_done_complete %>%
    summarise(unique_movie_ids = n_distinct(MovieID))

# Print the count of unique identifiers
print(unique_movie_ids_count)

write.csv(movie_ranks_not_done_complete, "movie_ranks_not_done_complete.csv")
