filtered_cast <- read_csv("gen/data-preparation/temp/no_url_in_master_cast.csv")


unique_id <- filtered_cast%>%
    distinct(`Movie ID`)


# Assuming 'filtered_cast' is your dataset
unique_actors <- filtered_cast %>%
    distinct(actor_imdb_id, .keep_all = TRUE)

write_csv(unique_actors, "unique_actors.csv")


