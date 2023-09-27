awards <- read.csv("../../../data/van_lin_datasets/imdb.com__awards.csv")
df <- read.csv("../../../gen/data-preparation/temp/final_master_everything.csv")

filtered_awards <- awards %>%
  filter(imdb.com_imdbid %in% df$imdb.com_imdbid)

# Step 1: Group filtered_awards by imdb.com_imdbid and imdb.com_award_outcome
filtered_awards_counts <- filtered_awards %>%
  group_by(imdb.com_imdbid, imdb.com_award_outcome) %>%
  summarize(count = n()) %>%
  pivot_wider(names_from = imdb.com_award_outcome, values_from = count, values_fill = 0)

df <- df %>%
  left_join(filtered_awards_counts, by = "imdb.com_imdbid")

write.csv(df , "../../../gen/data-preparation/temp/final_awards_added.csv")
