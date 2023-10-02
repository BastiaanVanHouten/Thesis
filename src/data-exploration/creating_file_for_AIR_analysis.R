# Load the necessary libraries
library(dplyr)

# Define the threshold for assigning a category (e.g., 0.5)
threshold <- 0.6

# Filter rows where 'asian' is not NA, currently 104412 have values
subset <- actors_with_ethnicity %>%
  filter(!is.na(asian))

# Assign individuals to race or ethnicity categories based on probabilities
subset <- subset %>%
  mutate(
    Assigned_Asian = ifelse(asian >= threshold, 1, 0),
    Assigned_Black = ifelse(black >= threshold, 1, 0),
    Assigned_Hispanic = ifelse(hispanic >= threshold, 1, 0),
    Assigned_White = ifelse(white >= threshold, 1, 0)
  )

subset <- subset %>%
  filter(
    any(Assigned_Asian == 1, Assigned_Black == 1, Assigned_Hispanic == 1, Assigned_White == 1)
  )

subset <- subset %>%
  select(- `Birth Year`, - asian, - black, -hispanic, - white, - age, - gender, - confidence , - actor_imdb_id, -`Cast Member Name`)

subset <- subset[, -c(1, 4)]

# Load the tidyr package
library(tidyr)

# Assuming your dataset is named "your_dataset", replace it with your actual dataset name
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

write.csv(subset, "Master/Thesis/gen/data-preparation/output/AIR_analysis.csv")
