# Load the necessary libraries
library(dplyr)

subset <- read_csv("../../data/actors_with_assigned_ethnicity.csv")



subset <- subset %>%
  filter(
    any(Assigned_Asian == 1, Assigned_Black == 1, Assigned_Hispanic == 1, Assigned_White == 1)
  )

subset <- subset %>%
  select(- `Birth.Year`, - asian, - black, -hispanic, - white, - age, - gender, - confidence , - actor_imdb_id, -`Cast.Member.Name`)

subset <- subset[, -c(1, 4)]

# Load the tidyr package
library(tidyr)

# Assuming your dataset is named replace it with your actual dataset name
subset <- subset %>%
  pivot_longer(
    cols = starts_with("Assigned_"),  # Select columns starting with "Assigned_"
    names_to = "Ethnicity",           # New column name
    values_to = "Assigned"            # New values column
  ) %>%
  mutate(
    Ethnicity = sub("Assigned_", "", Ethnicity),  # Remove "Assigned_" from the ethnicity names
    Assigned = ifelse(Assigned == 1, Ethnicity, "Not Assigned")  # Set Assigned to Ethnicity or "Not Assigned"
  ) %>%
  select(-Ethnicity)  # Remove the original Ethnicity column if needed

subset <- subset %>%
  filter(Assigned != "Not Assigned")

write.csv(subset, "../../gen/data-preparation/output/AIR_analysis.csv")
