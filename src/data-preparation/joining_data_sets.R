library(dplyr)
library(readr)

dir.create("gen/data-preparation/output", recursive = TRUE)

# Read the basics.csv and directors.csv files
basics <- read.csv("gen/data-preparation/temp/basics.csv")
directors <- read.csv("gen/data-preparation/temp/directors.csv")

# Perform a left join using the 'tconst' variable as the key
merged_data <- left_join(basics, directors, by = "tconst")

# Remove rows where data from directors.csv does not match basics.csv
merged_data <- merged_data[complete.cases(merged_data), ]

# View the resulting merged dataset
write_csv(merged_data, paste0('gen/data-preparation/output/', "merged_data.csv"))
 