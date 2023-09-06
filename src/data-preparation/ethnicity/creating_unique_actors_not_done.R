ethnicity_kairos <- read_csv("data/ethnicity_kairo_TMDB.csv")

cast_url <- read.csv("gen/data-preparation/temp/url_in_master_cast.csv")
cast <- read.csv("gen/data-preparation/temp/cast.csv")

no_url_cast <- cast %>%
    filter(Profile.Picture == "https://image.tmdb.org/t/p/w500None" & !is.na(actor_imdb_id))

unique_no_url_cast <- no_url_cast %>%
    distinct(actor_imdb_id, .keep_all = TRUE)

write.csv(unique_no_url_cast, "gen/data-preparation/temp/unique_no_url_cast.csv")



# making actors already ethnicity scraped
unique_actors_not_done <- unique_actors %>%
    filter(!`Profile Picture` %in% ethnicity_kairo_TMDB$image_url)

write.csv(unique_actors_not_done, "gen/data-preparation/temp/unique_actors_not_done.csv")
