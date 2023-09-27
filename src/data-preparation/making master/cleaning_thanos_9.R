library(dplyr)

thanos <- read.csv("../../../gen/data-preparation/temp/thanos_not_cleaned.csv")


# Removing the first 5 columms
thanos <- thanos %>%
  select(-(1:6))


# Specify the columns to remove
columns_to_remove <- c(
  "imdb.com_genres",
  "actor1",
  "actor2",
  "actor3",
  "actor4",
  "imdb.com_writer",
  "imdb.com_awards",
  "imdb.com_type",
  "Belongs.to.Collection",
  "n_one_asian",
  "n_one_black",
  "n_one_hisp",
  "n_one_white",
  "the_numbers_com_starpower_rank.x",
  "the_numbers_com_starpower_rank.y",
  "the_numbers_com_starpower_rank.x.x",
  "the_numbers_com_starpower_rank.y.y",
  "imdb.com_cast_id"
)

# Remove the specified columns
thanos <- thanos %>%
  select(-all_of(columns_to_remove))

write.csv(thanos, "../../../gen/data-preparation/output/thanos.csv")
