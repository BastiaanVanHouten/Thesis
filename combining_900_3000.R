
## combining 900 till 3000 

movie_ranks_900_2300 <- rbind(movie_ranks_900_1600, movie_ranks_1600_2300)

library(dplyr)

movie_ranks_900_2300_complete <- inner_join(movie_ranks_900_3000_1998_, movie_ranks_900_2300)
movie_ranks_2300_3000_complete <- inner_join(movie_ranks_900_3000_1998_, movie_ranks_2300_3000, by= "movie_id")


# Assuming you have two data frames: df1 and df2
# df1 has 1387 columns, df2 has 1335 columns

# Get the column names from df2
cols_to_keep <- colnames(movie_ranks_2300_3000_complete)

# Subset df1 to keep only the columns present in df2
movie_ranks_900_2300_subset <- movie_ranks_900_2300_complete[, cols_to_keep]


movie_ranks_900_3000 <- rbind(movie_ranks_900_2300_subset,movie_ranks_2300_3000_complete)

write_csv(movie_ranks_900_3000, "movie_ranks_900_3000.csv")
