library(readr)
library(dplyr)

# Read the data file
movies <- read_csv("C:/Users/Bas van Houten/Documents/Master/Thesis/data/kaggle/movies_metadata.csv")

# Filter movies based on release date and production country
us_production_movies_cleaned <- movies %>%
    filter(as.Date(release_date) > as.Date("1998-01-01")) %>%
    filter(grepl("US", production_countries)) %>%
    select(budget, genres, id, imdb_id, title, production_companies, production_countries, release_date, revenue, runtime, spoken_languages)

# Clean up the production_companies column
us_production_movies_cleaned$production_companies <- gsub("'name': '(.*?)', 'id': \\d+", "\\1", us_production_movies_cleaned$production_companies)
us_production_movies_cleaned$production_companies <- gsub("\\[|\\]", "", us_production_movies_cleaned$production_companies)
us_production_movies_cleaned$production_companies <- gsub("', '", ", ", us_production_movies_cleaned$production_companies)

# Convert production_countries format to comma-separated string
us_production_movies_cleaned$production_countries <- gsub("\\{'iso_3166_1': '(.*?)', 'name': '(.*?)'\\}", "\\1", us_production_movies_cleaned$production_countries)
us_production_movies_cleaned$production_countries <- gsub("\\[|\\]", "", us_production_movies_cleaned$production_countries)

# Convert genres format to comma-separated string
us_production_movies_cleaned$genres <- gsub("\\{'id': \\d+, 'name': '(.*?)'\\}", "\\1", us_production_movies_cleaned$genres)
us_production_movies_cleaned$genres <- gsub("\\[|\\]", "", us_production_movies_cleaned$genres)

# Remove animation and documentary from genres
us_production_movies_cleaned <- us_production_movies_cleaned %>%
    filter(!grepl("Animation|Documentary", genres, ignore.case = TRUE))

# Save the dataset
write_csv(us_production_movies_cleaned, file.path("gen", "data-preparation", "temp", "main_base.csv"))

    
