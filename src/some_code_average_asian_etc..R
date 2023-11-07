library(dplyr)

#Calculate the average confidence for Assigned_Asian = 1, ignoring NAs
average_asian_confidence <- actors_with_assigned_ethnicity %>%
  filter(Assigned_Asian == 1) %>%
  summarise(mean_confidence = mean(confidence, na.rm = TRUE))

# Calculate the average confidence for Assigned_Black = 1, ignoring NAs
average_black_confidence <- actors_with_assigned_ethnicity %>%
  filter(Assigned_Black == 1) %>%
  summarise(mean_confidence = mean(confidence, na.rm = TRUE))

# Calculate the average confidence for Assigned_Hispanic = 1, ignoring NAs
average_hispanic_confidence <- actors_with_assigned_ethnicity %>%
  filter(Assigned_Hispanic == 1) %>%
  summarise(mean_confidence = mean(confidence, na.rm = TRUE))

# Calculate the average confidence for Assigned_White = 1, ignoring NAs
average_white_confidence <- actors_with_assigned_ethnicity %>%
  filter(Assigned_White == 1) %>%
  summarise(mean_confidence = mean(confidence, na.rm = TRUE))

# Combine the results into a table
results_table <- data.frame(
  Ethnicity = c("Asian", "Black", "Hispanic", "White"),
  Average_Confidence = c(
    average_asian_confidence$mean_confidence,
    average_black_confidence$mean_confidence,
    average_hispanic_confidence$mean_confidence,
    average_white_confidence$mean_confidence
  )
)

# Print the table
print(results_table)

# Calculate the average confidence for Assigned_Asian = 0.5, ignoring NAs
average_asian_confidence_0_5 <- actors_with_assigned_ethnicity %>%
  filter(Assigned_Asian == 0.5) %>%
  summarise(mean_confidence = mean(confidence, na.rm = TRUE))

# Calculate the average confidence for Assigned_Black = 0.5, ignoring NAs
average_black_confidence_0_5 <- actors_with_assigned_ethnicity %>%
  filter(Assigned_Black == 0.5) %>%
  summarise(mean_confidence = mean(confidence, na.rm = TRUE))

# Calculate the average confidence for Assigned_Hispanic = 0.5, ignoring NAs
average_hispanic_confidence_0_5 <- actors_with_assigned_ethnicity %>%
  filter(Assigned_Hispanic == 0.5) %>%
  summarise(mean_confidence = mean(confidence, na.rm = TRUE))

# Calculate the average confidence for Assigned_White = 0.5, ignoring NAs
average_white_confidence_0_5 <- actors_with_assigned_ethnicity %>%
  filter(Assigned_White == 0.5) %>%
  summarise(mean_confidence = mean(confidence, na.rm = TRUE))

# Combine the results into a table
results_table_0_5 <- data.frame(
  Ethnicity = c("Asian", "Black", "Hispanic", "White"),
  Average_Confidence = c(
    average_asian_confidence_0_5$mean_confidence,
    average_black_confidence_0_5$mean_confidence,
    average_hispanic_confidence_0_5$mean_confidence,
    average_white_confidence_0_5$mean_confidence
  )
)

# Print the table for 0.5
print(results_table_0_5)

print(results_table)

