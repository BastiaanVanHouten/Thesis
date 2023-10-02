library(dplyr)
library(readr)

thanos <- read.csv("../../gen/data-preparation/output/thanos_endgame.csv")


# Create new columns based on conditions
thanos$T1_AIR_Asian <- ifelse(thanos$Total_Assigned_Asian < 1, 0, 1)
thanos$T1_AIR_Black <- ifelse(thanos$Total_Assigned_Black < 1, 0, 1)
thanos$T1_AIR_Hispanic <- ifelse(thanos$Total_Assigned_Hispanic < 1, 0, 1)
thanos$T1_AIR_White <- ifelse(thanos$Total_Assigned_White < 1, 0, 1)


# Assuming your dataset is named 'thanos'

# Count the number of ones in each column, and make it robust against NAs
count_ones_asian <- sum(thanos$T1_AIR_Asian == 1, na.rm = TRUE)
count_ones_black <- sum(thanos$T1_AIR_Black == 1, na.rm = TRUE)
count_ones_hispanic <- sum(thanos$T1_AIR_Hispanic == 1, na.rm = TRUE)
count_ones_white <- sum(thanos$T1_AIR_White == 1, na.rm = TRUE)

# Print the counts
cat("Count of ones in T1_AIR_Asian:", count_ones_asian, "\n")
cat("Count of ones in T1_AIR_Black:", count_ones_black, "\n")
cat("Count of ones in T1_AIR_Hispanic:", count_ones_hispanic, "\n")
cat("Count of ones in T1_AIR_White:", count_ones_white, "\n")


