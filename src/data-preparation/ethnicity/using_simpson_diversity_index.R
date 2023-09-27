# Load the necessary libraries
library(dplyr)

actors_with_ethnicity <- read.csv("../../../gen/data-preparation/output/actors_with_ethnicity.csv")


comparing <- actors_with_ethnicity %>%
    filter(!is.na(asian) & !grepl("uncredited", Character, ignore.case = TRUE))

# first clean for uncredited and asian is not NA
subset <- actors_with_ethnicity %>%
    filter(!is.na(asian) & !grepl("uncredited", Character, ignore.case = TRUE))



# Define the thresholds
threshold_high <- 0.6
threshold_low <- 0.25

# Assign individuals to race or ethnicity categories based on probabilities
subset <- subset %>%
    mutate(
        Assigned_Asian = ifelse(asian >= threshold_high, 1,
                                ifelse(asian >= threshold_low, 0.5, 0)),
        Assigned_Black = ifelse(black >= threshold_high, 1,
                                ifelse(black >= threshold_low, 0.5, 0)),
        Assigned_Hispanic = ifelse(hispanic >= threshold_high, 1,
                                   ifelse(hispanic >= threshold_low, 0.5, 0)),
        Assigned_White = ifelse(white >= threshold_high, 1,
                                ifelse(white >= threshold_low, 0.5, 0))
    )


# Assuming actors_with_ethnicity is your data frame
# Specify the columns you want to calculate the average for
columns_to_average <- c("asian", "black", "hispanic", "white")

# Use rowMeans to calculate the average for each row in these columns
average_ethnicity <- rowMeans(actors_with_ethnicity[columns_to_average], na.rm = TRUE)

# average_ethnicity now contains the average for each row in the specified columns


# Assuming actors_with_ethnicity is your data frame
# Specify the columns you want to visualize
columns_to_visualize <- c("asian", "black", "hispanic", "white")

# Create histograms for each column within the range [0, 0.5]
par(mfrow = c(2, 2))  # Arrange plots in a 2x2 grid

for (col in columns_to_visualize) {
    # Filter the data within the specified range [0, 0.5]
    data_filtered <- actors_with_ethnicity[[col]][actors_with_ethnicity[[col]] >= 0 & actors_with_ethnicity[[col]] <= 1]
    
    # Create histogram without frequencies (percentages)
    hist(data_filtered, main = col, xlab = col, col = "lightblue", freq = FALSE)
    
    # Calculate the percentage of data points in each bin
    breaks <- hist(data_filtered, plot = FALSE)$breaks
    counts <- hist(data_filtered, plot = FALSE)$counts
    percent <- round(100 * counts / sum(counts), 2)
    
    # Add percentage labels to the plot
}

# Reset the plotting layout to default
par(mfrow = c(1, 1))


# Assuming actors_with_ethnicity is your data frame
# Specify the columns you want to analyze
columns_to_analyze <- c("asian", "black", "hispanic", "white")

# Initialize an empty vector to store the percentages
percentages_below_0.5 <- numeric(length(columns_to_analyze))

# Calculate the percentage of values below 0.5 for each column
for (i in 1:length(columns_to_analyze)) {
    column <- subset[[columns_to_analyze[i]]]
    percentages_below_0.5[i] <- 100 * sum(column > 0.60, na.rm = TRUE) / length(column)
}



subset <- subset %>%
    filter(
        Assigned_Asian >= 0.5 | Assigned_Black >=  0.5 | Assigned_Hispanic >=  0.5 | Assigned_White >=  0.5
    )

subset_movies <- subset %>%
    group_by(`Movie.ID`) %>%
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



write.csv(subset_movies_simpson, "../../../gen/data-preparation/output/movies_simpson_index.csv")
