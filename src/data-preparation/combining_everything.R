library(dplyr)
library(readr)

MASTER_2000_2020.csv <- read_csv("data/MASTER_2000-2020.csv")
main_base <- read_csv("gen/data-preparation/temp/main_base.csv")
scraped_budgets_imdb <- read_csv("data/scraped/scraped_budgets_imdb.csv")
scraped_budgets_TMDB <- read_csv("data/scraped/movie_budget_revenue_sequal_TMDB.csv")
awards_ratings <- read_csv("gen/data-preparation/temp/awards_ratings.csv")


combined <- full_join(main_base, MASTER_2000_2020.csv, by = c("imdb_id" = "imdb.com_imdbid"))
combined_with_budget <- full_join(combined, scraped_budgets_imdb, by = c("imdb_id" = "Movie ID"))
combined_everything <- full_join(combined_with_budget, scraped_budgets_TMDB, by = c("title" = "Title"))
final_dataset <- full_join(combined_everything , awards_ratings, by = c("imdb_id" = "IMDb ID"))


# Changing "Not available" in Budget.x and NA in Budget.y to zeros
final_dataset <- final_dataset %>%
    mutate(
        Budget.x = ifelse(Budget.x == 'Not available', 0, Budget.x),
        Budget.y = ifelse(is.na(Budget.y), 0, Budget.y),
        boxofficemojo.com_budget = ifelse(is.na(boxofficemojo.com_budget), 0, boxofficemojo.com_budget)
    )



# Assuming 'final_dataset' is your dataset
filtered_final_dataset <- final_dataset %>%
    filter(
        !is.na(`boxofficemojo.com_openingtheaters`) & `boxofficemojo.com_openingtheaters` != "",
        !is.na(`boxofficemojo.com_openinggross`) & `boxofficemojo.com_openinggross` != "",
        !is.na(`imdb.com_sequel`) & `imdb.com_sequel` != "",
        !is.na(`imdb.com_basedonbook`) & `imdb.com_basedonbook` != "",
        !is.na(`imdb.com_basedonshortstory`) & `imdb.com_basedonshortstory` != "",
        !is.na(`imdb.com_basedonnovel`) & `imdb.com_basedonnovel` != "",
        !is.na(`imdb.com_basedontvmovie`) & `imdb.com_basedontvmovie` != "",
        !is.na(`imdb.com_basedonplay`) & `imdb.com_basedonplay` != "",
        !is.na(`imdb.com_basedontvseries`) & `imdb.com_basedontvseries` != "",
        !is.na(`imdb.com_spinoff`) & `imdb.com_spinoff` != "",
        !is.na(`imdb.com_remake`) & `imdb.com_remake` != "",
        !is.na(`imdb.com_basedonbookseries`) & `imdb.com_basedonbookseries` != "",
        !is.na(`imdb.com_basedoncomic`) & `imdb.com_basedoncomic` != "",
        !is.na(`imdb.com_basedoncomicbook`) & `imdb.com_basedoncomicbook` != "",
        !is.na(`production_companies`) & `production_companies` != "",
        imdb.com_year >= 1998 & imdb.com_year <= 2019,
        
    )

filtered_final_dataset$imdb.com_basedonbook

# Using names() function
column_names <- names(filtered_final_dataset)

# Using colnames() function (works the same as names())
column_names <- colnames(filtered_final_dataset)

print(column_names)

unique(filtered_final_dataset$imdb.com_year)

# Check the data types and identify non-numeric values
str(filtered_final_dataset)       

filtered_final_dataset_budget <- filtered_final_dataset %>%
    mutate(
        budget = as.numeric(gsub("\\$", "", budget)),
        boxofficemojo.com_budget = as.numeric(gsub("[^0-9.]", "", boxofficemojo.com_budget)),
        Budget.x = as.numeric(gsub("\\$", "", Budget.x)), # Remove "$" sign
        Budget.x = ifelse(Budget.x == "Not available" | is.na(Budget.x), 0, Budget.x), # Replace "Not available" and NA with 0
        Budget.y = as.numeric(gsub("\\$", "", Budget.y)),
        total_budget = budget + boxofficemojo.com_budget + Budget.x + Budget.y,
        count_non_missing = rowSums(!is.na(select(., c('budget', 'boxofficemojo.com_budget', 'Budget.x', 'Budget.y')))),
        average_budget = total_budget / count_non_missing
    )


unique(filtered_final_dataset_budget$average_budget)





# Check the data types and identify non-numeric values
str(filtered_final_dataset_budget)        
        

# Count the number of observations with 0 or NA values in all four variables 
count_zero_all_budgets_tmdb <- sum(
    rowSums(combined_everything[, c('budget', 'boxofficemojo.com_budget', 'Budget.x','Budget.y' )] == 0 | 
                is.na(combined_everything[, c('budget', 'boxofficemojo.com_budget', 'Budget.x','Budget.y' )])) == 4
)

library(dplyr)

# Assuming 'combined_everything' is your dataset
filtered_movies <- final_dataset %>%
    filter(
        rowSums(
            select(., c('budget', 'boxofficemojo.com_budget', 'Budget.x', 'Budget.y')) == 0 | 
                is.na(select(., c('budget', 'boxofficemojo.com_budget', 'Budget.x', 'Budget.y')))
        ) != 4
    )



# Assuming 'combined_everything' is your dataset
filtered_movies <- final_dataset %>%
    filter(
        rowSums(
            select(., c('budget', 'boxofficemojo.com_budget', 'Budget.x', 'Budget.y')) == 0 | 
                is.na(select(., c('budget', 'boxofficemojo.com_budget', 'Budget.x', 'Budget.y')))
        ) != length(c('budget', 'boxofficemojo.com_budget', 'Budget.x', 'Budget.y'))
    )



all_togheter <- full_join(main_base, )