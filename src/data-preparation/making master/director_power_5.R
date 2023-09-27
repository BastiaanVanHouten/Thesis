library(readr)
imdb_com_cast_1 <- read_csv("../../../data/van_lin_datasets/imdb.com__cast_1.csv")
imdb_com_cast_2 <- read_csv("../../../data/van_lin_datasets/imdb.com__cast_2.csv")
imdb_com_cast_3 <- read_csv("../../../data/van_lin_datasets/imdb.com__cast_3.csv")
imdb_com_cast_4 <- read_csv("../../../data/van_lin_datasets/imdb.com__cast_4.csv")

df <- read.csv("../../../gen/data-preparation/temp/final_ranks_actors_power.csv")

# Create a vector of imdb.com_imdbid values from df
imdb_ids_to_include <- df$imdb.com_imdbid

# Filter each data frame separately
imdb_com_cast_1 <- imdb_com_cast_1 %>%
  filter(imdb.com_imdbid %in% imdb_ids_to_include, imdb.com_cast_cat == "Directed by")

imdb_com_cast_2 <- imdb_com_cast_2 %>%
  filter(imdb.com_imdbid %in% imdb_ids_to_include, imdb.com_cast_cat == "Directed by")

imdb_com_cast_3 <- imdb_com_cast_3 %>%
  filter(imdb.com_imdbid %in% imdb_ids_to_include, imdb.com_cast_cat == "Directed by")

imdb_com_cast_4 <- imdb_com_cast_4 %>%
  filter(imdb.com_imdbid %in% imdb_ids_to_include, imdb.com_cast_cat == "Directed by")

imdb_com_cast_1 <- imdb_com_cast_1[, -5]

# Combine the filtered data frames into a single data frame
combined_df <- bind_rows(
  imdb_com_cast_1,
  imdb_com_cast_2,
  imdb_com_cast_3,
  imdb_com_cast_4
)

director_power <- read.csv("../../../data/van_lin_datasets/the-numbers.com_directors.csv")

# Perform the left join
result_df <- df %>%
  left_join(
    combined_df %>% select(-`imdb.com_cast_cat`), 
    by = c("imdb.com_imdbid" = "imdb.com_imdbid", "imdb.com_director" = "imdb.com_cast_name")
  )


result_df <- result_df %>%
  left_join(
    director_power %>%
      select(year, imdb_com_director_id, the_numbers_com_dirpower_rank),
    by = c("imdb.com_year" = "year",
           "imdb.com_cast_id" = "imdb_com_director_id")
  )

write.csv(result_df, "../../../gen/data-preparation/temp/final_master_everything.csv")
