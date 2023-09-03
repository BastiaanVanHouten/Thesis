ethnicity_kairos <- read_csv("data/ethnicity_kairo_TMDB.csv")


# making actors already ethnicity scraped
unique_actors_not_done <- unique_actors %>%
    filter(!`Profile Picture` %in% ethnicity_kairo_TMDB$image_url)

write.csv(unique_actors_not_done, "gen/data-preparation/temp/unique_actors_not_done.csv")
