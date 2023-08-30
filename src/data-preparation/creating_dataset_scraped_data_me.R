everything_me <- full_join(main_base, scraped_budgets_imdb, by = c("imdb_id" = "Movie ID"))

everything_me_final <- full_join(everything_me, awards_ratings, by = c("imdb_id" = "IMDb ID"))

everything_me_final_directors <- inner_join(everything_me_final, directors , by = c("imdb_id" = "tconst"))

everything_me_final_actors <- inner_join(everything_me_final_directors, movie_budget_revenue_sequal_TMDB , by = c("title" = "Title") )


# Count the number of incomplete cases in the everything_me_final_actors dataframe
incomplete_count <- sum(!complete.cases(everything_me_final_actors))

# Print the count
cat("Number of incomplete cases in everything_me_final_actors:", incomplete_count, "\n")


# Replace 'Not available' with 0 in the 'Budget' column
final_movie_dataset_scraped <- everything_me_final_actors %>%
    mutate(Budget.x = ifelse(Budget.x == 'Not available', 0, Budget.x))

# Count the number of observations with 0 or NA values in all three variables
count_zero_na_all_budgets <- sum(
    rowSums(final_movie_dataset_scraped[, c('budget', 'Budget.y', 'Budget.x')] == 0 | 
                is.na(final_movie_dataset_scraped[, c('budget', 'Budget.y', 'Budget.x')])) == 3
)

# Print the count
cat("Number of observations with 0 or NA values in any budget-related variables:", count_zero_na_all_budgets, "\n")
