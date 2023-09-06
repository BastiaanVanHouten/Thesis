library(dplyr)
library(tidyverse)



ethnicity_IMDB_TMDB <- rbind(ethnicity_kairo_IMDB, ethnicity_kairo_TMDB)

# Create a logical vector to identify rows where Profile Picture is equal to the specific value
condition <- cast$`Profile Picture` == "https://image.tmdb.org/t/p/w500None"

# Replace the matching rows with NA
cast$`Profile Picture`[condition] <- NA


cast_added_imdb_url <- left_join(cast, actor_url_imdb, by = c("actor_imdb_id" = "IMDb ID"))


cast_added_imdb_url$`Profile Picture` <- ifelse(
    is.na(cast_added_imdb_url$`Profile Picture`),
    cast_added_imdb_url$`Second Image URL`,
    cast_added_imdb_url$`Profile Picture`
)



cast_added_imdb_url <- cast_added_imdb_url %>%
    select(-`Second Image URL`)

# Remove duplicates based on the image_url column
ethnicity_IMDB_TMDB <- distinct(ethnicity_IMDB_TMDB, image_url, .keep_all = TRUE)

ethnicity_with_cast <- left_join(cast_added_imdb_url,ethnicity_IMDB_TMDB , by = c("Profile Picture" = "image_url"))


# Count the number of NA values in the Profile Picture column
na_count <- sum(is.na(cast_added_imdb_url$`Profile Picture`))

# Print the count of NA values
cat("Number of NA values in the Profile Picture column:", na_count, "\n")

ethnicity_with_cast <- ethnicity_with_cast %>%
    filter(`Movie ID` %in% filtered_final_dataset_budget$`boxofficemojo.com_imdbid`)

write.csv(ethnicity_with_cast, "data/cast_ethnicity/the_final_ethnicity_file.csv")

