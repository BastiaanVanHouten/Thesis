final_movie_dataset <- inner_join(main_base, MASTER_2000_2020, by = c("imdb_id" = "imdb.com_imdbid"))


final_movie_dataset_awards <- left_join(final_movie_dataset, awards_ratings, by = c("imdb_id" = "IMDb ID"))

final_movie_dataset_imdb_budget <- left_join(final_movie_dataset_awards, scraped_budgets, by = c("imdb_id" = "Movie ID"))



# Replace 'Not available' with 0 in the 'Budget' column
final_movie_dataset_imdb_budget <- final_movie_dataset_imdb_budget %>%
    mutate(Budget = ifelse(Budget == 'Not available', 0, Budget))


# Count the number of observations with 0 or NA values in all three variables
count_zero_na_all_budgets <- sum(
    rowSums(final_movie_dataset_imdb_budget[, c('budget', 'boxofficemojo.com_budget', 'Budget')] == 0 | 
                is.na(final_movie_dataset_imdb_budget[, c('budget', 'boxofficemojo.com_budget', 'Budget')])) == 3
)

# Print the count
cat("Number of observations with 0 or NA values in all budget-related variables:", count_zero_na_all_budgets, "\n")




# Count the number of NA values in the boxofficemojo.com_openingtheaters column
na_count_opening_theaters <- sum(is.na(final_movie_dataset$`boxofficemojo.com_budget`))

# Print the count
cat("Number of NA values in boxofficemojo.com_openingtheaters column:", na_count_opening_theaters, "\n")




# Count the number of 0 values in the 'Budget' column
count_zeros_budget <- sum(final_movie_dataset_imdb_budget$Budget == 0)

# Print the count
cat("Number of 0 values in 'Budget' column:", count_zeros_budget, "\n")


# Count the number of 0 values in the 'Budget' column
count_zeros_budget <- sum(final_movie_dataset_imdb_budget$budget == 0)

# Print the count
cat("Number of 0 values in 'Budget' column:", count_zeros_budget, "\n")


# Count the number of 0 values in the 'Budget' column
count_zeros_budget <- sum(scraped_budgets_imdb$Budget == "Not available")

# Print the count
cat("Number of 0 values in 'Budget' column:", count_zeros_budget, "\n")



