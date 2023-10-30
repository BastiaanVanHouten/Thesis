library(dplyr)
library(readr)
library(tidyr)

actors_ass_ethnicity <- read_csv("../../../gen/data-preparation/output/AIR_analysis")

df <- actors_ass_ethnicity  %>%
  select(- `Birth.Year`, - asian, - black, -hispanic, - white, - age, - gender, - confidence , - actor_imdb_id, -`Cast.Member.Name`)

df <- df[, -c(1, 2, 5)]


# Assuming your dataset is named "your_dataset", replace it with your actual dataset name
df <- df %>%
  pivot_longer(
    cols = starts_with("Assigned_"),  # Select columns starting with "Assigned_"
    names_to = "Ethnicity",           # New column name
    values_to = "Assigned"            # New values column
  ) %>%
  mutate(
    Ethnicity = sub("Assigned_", "", Ethnicity),  # Remove "Assigned_" from the ethnicity names
    Assigned = case_when(
      Assigned >= 0.5 ~ Ethnicity,
      TRUE ~ "Not Assigned"
    )
  ) %>%
  select(-Ethnicity)  # Remove the original Ethnicity column if needed

df <- df %>%
  filter(Assigned != "Not Assigned")

write.csv(df, "../../../gen/data-preparation/output/characters_ass_long.csv")

## proceed to jupyter notebook and follow up with named_characters.csv

library(dplyr)

named_characters <- read_csv("../../../named_characters.csv")

# Pivot your data and create 8 new columns
named_characters <- named_characters %>%
  pivot_wider(
    names_from = Assigned,
    values_from = Assigned
  ) 

library(dplyr)

# Replace all non-NA values in the ethnicity columns with 1 and NA with 0
named_characters <- named_characters %>%
    mutate(
        Black = ifelse(!is.na(Black), 1, 0),
        White = ifelse(!is.na(White), 1, 0),
        Asian = ifelse(!is.na(Asian), 1, 0),
        Hispanic = ifelse(!is.na(Hispanic), 1, 0)
    )



subset_movies_named <- named_characters %>%
    group_by(Movie.ID) %>%
    dplyr::summarize(
        Total_Assigned_Asian = sum(Asian, na.rm = TRUE),
        Total_Assigned_Black = sum(Black, na.rm = TRUE),
        Total_Assigned_Hispanic = sum(Hispanic, na.rm = TRUE),
        Total_Assigned_White = sum(White, na.rm = TRUE)
    )



subset_movies_named  <- subset_movies_named  %>%
  mutate(total_people = Total_Assigned_Asian + Total_Assigned_Black + Total_Assigned_Hispanic +  Total_Assigned_White)


subset_movies_simpson_named  <- subset_movies_named %>%
  mutate(n_one_asian = (Total_Assigned_Asian - 1) * Total_Assigned_Asian, 
         n_one_black = (Total_Assigned_Black - 1) * Total_Assigned_Black,
         n_one_hisp = (Total_Assigned_Hispanic - 1) * Total_Assigned_Hispanic,
         n_one_white = (Total_Assigned_White - 1) * Total_Assigned_White)

subset_movies_simpson_named <-subset_movies_simpson_named%>%
  filter(total_people != 1)
  
  
subset_movies_simpson_named  <- subset_movies_simpson_named  %>%
  mutate(D = (n_one_asian + n_one_black +  n_one_hisp + n_one_white) /  (total_people * ( total_people - 1 )))

subset_movies_simpson_named <- subset_movies_simpson_named %>%
  mutate(simpson_index = 1 - D)

write.csv(subset_movies_simpson_named, "../../../gen/data-preparation/output/movies_simpson_named.csv")

# Calculate the average value for the "simpson_index" column
average_simpson_index_named <- mean(subset_movies_simpson_named$simpson_index, na.rm = TRUE)

# Print the result
cat("Average Simpson Index:", average_simpson_index_named, "\n")


# Double check the amount of people that did not have an image and where named characters.
actors_with_ethnicity <- read.csv("../../../gen/data-preparation/output/actors_with_ethnicity.csv")


check_named_char_no_image <- named_characters %>%
    left_join(actors_with_ethnicity, by = c("Movie.ID", "Character")) %>%
    select(Movie.ID, Character, confidence)%>%
    distinct()

na_count <- sum(is.na(check_named_char_no_image$confidence))

na_count_original <- sum(is.na(actors_with_ethnicity$confidence))



