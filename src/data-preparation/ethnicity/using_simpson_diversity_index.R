# Load the necessary libraries
library(dplyr)

# Define the threshold for assigning a category (e.g., 0.5)
threshold <- 0.5

# Filter rows where 'asian' is not NA, currently 104412 have values
subset <- the_final_ethnicity_file %>%
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

subset_movies <- subset %>%
    group_by(`Movie ID`) %>%
    summarize(
        Total_Assigned_Asian = sum(Assigned_Asian),
        Total_Assigned_Black = sum(Assigned_Black),
        Total_Assigned_Hispanic = sum(Assigned_Hispanic),
        Total_Assigned_White = sum(Assigned_White)
    )


subset_movies <- subset_movies %>%
    mutate(total_people = Total_Assigned_Asian + Total_Assigned_Black + Total_Assigned_Hispanic +  Total_Assigned_White)


subset_movies_simpson <- subset_movies %>%
    mutate(n_one_asian = (Total_Assigned_Asian - 1) * Total_Assigned_Asian, 
           n_one_black = (Total_Assigned_Black - 1) * Total_Assigned_Black,
           n_one_hisp = (Total_Assigned_Hispanic - 1) * Total_Assigned_Hispanic,
           n_one_white = (Total_Assigned_White - 1) * Total_Assigned_White)

subset_movies_simpson <- subset_movies_simpson %>%
    mutate(D = (n_one_asian + n_one_black +  n_one_hisp + n_one_white) /  (total_people * ( total_people - 1 )))

subset_movies_simpson <- subset_movies_simpson %>%
    mutate(simpson_index = 1 - D)



write.csv(subset_movies_simpson, "gen/data-preparation/movies_simpson_index.csv")
