# Assuming you have the 'tidyr' package loaded
library(tidyr)
library(dplyr)

the_numbers_com_stars <- read.csv("../../../data/van_lin_datasets/the-numbers.com_stars.csv")
final_master_ranks <- read.csv("../../../gen/data-preparation/temp/master_with_simpson.csv")

# Split the 'actors' column by commas into separate columns
final_master_ranks <- final_master_ranks %>%
  separate(imdb.com_actors, into = c("actor1", "actor2", "actor3", "actor4"), sep = ", ")


# Join the two datasets based on release year and actors' names
result <- final_master_ranks %>%
  left_join(the_numbers_com_stars %>%
              select(year, imdb_com_star_name, the_numbers_com_starpower_rank), 
            by = c("imdb.com_year" = "year", 
                   "actor1" = "imdb_com_star_name")) %>%
  left_join(the_numbers_com_stars %>%
              select(year, imdb_com_star_name, the_numbers_com_starpower_rank), 
            by = c("imdb.com_year" = "year", 
                   "actor2" = "imdb_com_star_name")) %>%
  left_join(the_numbers_com_stars %>%
              select(year, imdb_com_star_name, the_numbers_com_starpower_rank), 
            by = c("imdb.com_year" = "year", 
                   "actor3" = "imdb_com_star_name")) %>%
  left_join(the_numbers_com_stars %>%
              select(year, imdb_com_star_name, the_numbers_com_starpower_rank), 
            by = c("imdb.com_year" = "year", 
                   "actor4" = "imdb_com_star_name"))

# Calculate the total "star power" for each movie
result <- result %>%
  mutate(Total_Star_Power = rowSums(select(., starts_with("the_numbers_com_starpower_rank")), na.rm = TRUE))

# View the updated dataset with the total "star power" column
head(result)


write.csv(result, "../../../gen/data-preparation/temp/final_ranks_actors_power.csv")
