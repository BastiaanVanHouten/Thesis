library(tidyverse)
library(readr)

ethniccelebs <- read_csv("data/scraped/ethniccelebs_data.csv")
info_actors <- read_csv("gen/data-preparation/temp/info_actors.csv")

# Assuming your dataset is called "ethniccelebs"
na_count <- sum(ethniccelebs$Ethnicity == "N/A", na.rm = TRUE)

ethniccelebs <- ethniccelebs %>%
    filter(Ethnicity != "N/A")

# Assuming your dataset is called "your_dataset" and the column is named "Name"
ethniccelebs$Name <- tools::toTitleCase(ethniccelebs$Name)

# Assuming your dataset is called "ethniccelebs" and the column is named "Birth Year"
ethniccelebs$`Birth Year` <- as.character(ethniccelebs$`Birth Year`)

# Match the datasets based on primaryName and birthYear
merged_data <- merge(info_actors, ethniccelebs, by.x = c("primaryName", "birthYear"), by.y = c("Name", "Birth Year"), all.x = TRUE)


# Remove unnecessary columns
merged_data <- merged_data[, !(names(merged_data) %in% c("Ethnicity.y"))]

# Rename the merged column to "Ethnicity"
colnames(merged_data)[colnames(merged_data) == "Ethnicity.x"] <- "Ethnicity"

# Resulting dataset with added values
dataset_ethniccelebs_info <- merged_data


# save dataset
write_csv(dataset_ethniccelebs_info, paste0('gen/data-preparation/temp/', "info_actors_.csv"))
