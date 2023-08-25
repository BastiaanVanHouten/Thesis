# Assuming movie_ranks is your dataset
# Check for duplicates in the "movie_id" column
duplicates <- movie_ranks[duplicated(movie_ranks$movie_id), ]

# Show the rows with duplicate movie_ids
print(duplicates)

# Remove duplicates from the "movie_id" column
unique_movie_ranks <- movie_ranks[!duplicated(movie_ranks$movie_id), ]


# Assuming main_base is your dataset
# Count observations with no NAs or zeros
valid_observations <- main_base[complete.cases(main_base) & !apply(main_base == 0, 1, all), ]
num_valid_observations <- nrow(valid_observations)

# Print the number of valid observations
print(num_valid_observations)
