library(dplyr)
library(tidyverse)



ethnicity_IMDB_TMDB <- read.csv("../../../data/cast_ethnicity/kairos_based_on_urls_TMDB_IMDB.csv")
actor_url_imdb <- read.csv("../../../data/cast_ethnicity/noTMDB_url_actor_url_IMDB.csv")
actor_url_tmdb <- read.csv("../../../data/cast_ethnicity/TMDB_url_only.csv")
cast <- read.csv("../../../data/cast_ethnicity/movie_cast.csv")

# Remove duplicates from actor_url_imdb
actor_url_imdb <- actor_url_imdb %>%
    distinct()

# Remove duplicates from actor_url_tmdb
actor_url_tmdb <- actor_url_tmdb %>%
    distinct()


cast <- cast %>%
    left_join(actor_url_tmdb %>% select(actor_imdb_id, Profile.Picture), by = "actor_imdb_id")


# Create a logical vector to identify rows where Profile Picture is equal to the specific value
condition <- cast$`Profile Picture` == "https://image.tmdb.org/t/p/w500None"

# Replace the matching rows with NA
cast$`Profile Picture`[condition] <- NA


cast_added_imdb_url <- left_join(cast, actor_url_imdb, by = c("actor_imdb_id" = "IMDb.ID"))


cast_added_imdb_url$`Profile.Picture` <- ifelse(
    is.na(cast_added_imdb_url$`Profile.Picture`),
    cast_added_imdb_url$`Second.Image.URL`,
    cast_added_imdb_url$`Profile.Picture`
)


cast_added_imdb_url <- cast_added_imdb_url %>%
    select(-`Second.Image.URL`)

# Remove duplicates based on the image_url column
ethnicity_IMDB_TMDB <- distinct(ethnicity_IMDB_TMDB, image_url, .keep_all = TRUE)

ethnicity_with_cast <- left_join(cast_added_imdb_url,ethnicity_IMDB_TMDB , by = c("Profile.Picture" = "image_url"))

# reading in thanos
thanos <- read_csv("../../../gen/data-preparation/output/thanos.csv")

ethnicity_with_cast <- ethnicity_with_cast %>%
    filter(`Movie.ID` %in% thanos$`boxofficemojo.com_imdbid`)

write.csv(ethnicity_with_cast, "../../../gen/data-preparation/temp/ethnicity_kairos_thanos.csv")

