library(dplyr)


movie_cast <- unique(movie_cast)
the_final_ethnicity_file <- unique(the_final_ethnicity_file)


# Left join by multiple variables (actor_imdb_id and movie_id)
cast_with_ethnicity <- left_join(movie_cast, the_final_ethnicity_file, by = c("actor_imdb_id", "Cast Member Name", "Movie ID"))
cast_without_ethnicity <- cast_with_ethnicity %>%
  filter(is.na(asian))

library(dplyr)

cast_filtered <- cast_without_ethnicity %>%
  filter(is.na(actor_imdb_id))



movie_cast_with_url <- cast_with_ethnicity %>%
  filter(!is.na(`Profile Picture`)) %>%
  filter(is.na(asian))


write.csv(movie_cast_with_url, "Master/Thesis/final_kairos_set.csv")
