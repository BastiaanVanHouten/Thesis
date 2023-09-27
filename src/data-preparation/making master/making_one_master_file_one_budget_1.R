library(dplyr)
library(readr)

MASTER_2000_2020 <- read_csv("data/MASTER_2000-2020.csv")
scraped_budgets_imdb <- read_csv("data/scraped/additional_budgets/scraped_budgets_imdb.csv")
scraped_budgets_TMDB <- read_csv("data/scraped/additional_budgets/movie_budget_revenue_sequal_TMDB.csv")
awards_ratings <- read_csv("gen/data-preparation/temp/awards_ratings.csv")

#Filtering away animation, year, no opening screens and USA
MASTER_2000_2020 <- MASTER_2000_2020 %>%
    filter(
        !grepl("Animation", boxofficemojo.com_genres, ignore.case = TRUE) &
            grepl("USA", imdb.com_country, ignore.case = TRUE) &
            !is.na(boxofficemojo.com_openingtheaters) &
            imdb.com_year >= 1998 &
            imdb.com_year <= 2019
    )



# Remove duplicates based on the ID column scraped_budgets
scraped_budgets_imdb <- distinct(scraped_budgets_imdb, `Movie ID`, .keep_all = TRUE)


# Remove duplicates based on the ID column scraped_budgets
scraped_budgets_TMDB <- distinct(scraped_budgets_TMDB, `Title`, .keep_all = TRUE)



# adding the awards and the budgets 
combined_budget_IMDB <- left_join(MASTER_2000_2020, scraped_budgets_imdb, by = c("imdb.com_imdbid" = "Movie ID"))
combined_budget_TMDB_IMDB <- left_join(combined_budget_IMDB, scraped_budgets_TMDB, by = c("imdb.com_title" = "Title"))
final_dataset <- left_join(combined_budget_TMDB_IMDB , awards_ratings, by = c("imdb.com_imdbid" = "IMDb ID"))

# 7759 observation after removing duplicatess imdb id
final_dataset <- final_dataset %>%
    distinct(`imdb.com_imdbid`, .keep_all = TRUE)


# Changing "Not available", NA and NA in the budgets to zeros
final_dataset <- final_dataset %>%
    mutate(
        Budget.x = ifelse(Budget.x == 'Not available' | is.na(Budget.x), 0, Budget.x),
        Budget.y = ifelse(is.na(Budget.y), 0, Budget.y),
        boxofficemojo.com_budget = ifelse(is.na(boxofficemojo.com_budget), 0, boxofficemojo.com_budget)
    )


#filter for having at least one budget, around 4247 movies left
final_dataset_has_budget <- final_dataset %>%
    filter(Budget.x != 0 | Budget.y != 0 | boxofficemojo.com_budget != 0)


# Making one budget value
filtered_final_dataset_budget <- final_dataset_has_budget %>%
    mutate(
        boxofficemojo.com_budget = as.numeric(gsub("[^0-9.]", "", boxofficemojo.com_budget)),
        Budget.x = as.character(Budget.x),  # Ensure it's character type
        Budget.x = ifelse(Budget.x == "Not available" | is.na(Budget.x), "0", Budget.x),  # Replace with "0"
        Budget.x = ifelse(!grepl("^\\$?[0-9,.]+$", Budget.x), "0", Budget.x),  # Replace non-numeric values with "0"
        Budget.x = as.numeric(gsub("[^0-9.]", "", Budget.x)),  # Convert to numeric
        Budget.y = as.numeric(gsub("\\$", "", Budget.y)),
        total_budget = boxofficemojo.com_budget + Budget.x + Budget.y,
        count_non_missing = rowSums(select(., c('boxofficemojo.com_budget', 'Budget.x', 'Budget.y')) != 0),
        average_budget = ifelse(count_non_missing == 0, 0, total_budget / count_non_missing)
    )



write.csv(filtered_final_dataset_budget, "gen/data-preparation/temp/master.csv")
