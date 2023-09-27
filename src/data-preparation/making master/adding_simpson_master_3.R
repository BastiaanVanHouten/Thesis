library(dply)

master_cleaned <- read_csv("../../../gen/data-preparation/temp/master_cleaned.csv")
subset_movies_simpson <- read.csv("../../../gen/data-preparation/output/movies_simpson_index.csv")

master_with_simpson <- left_join(master_cleaned, subset_movies_simpson, by = c("imdb.com_imdbid" = "Movie.ID"))

write.csv(master_with_simpson, "../../../gen/data-preparation/temp/master_with_simpson.csv")
