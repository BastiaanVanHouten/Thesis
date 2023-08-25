# Read in dataset ethnicity of wikipedia
ethnicity_data <- read_csv("data/consolidated_data.csv")

ethnicity_data$Ethnicity <- gsub("List of", "", ethnicity_data$Ethnicity)
ethnicity_data$Ethnicity <- gsub("actors", "", ethnicity_data$Ethnicity)

ethnicity_data <- subset(ethnicity_data, Name %in% name_actors$primaryName)

info_actors <- left_join(name_actors, ethnicity_data, by = c("primaryName" = "Name", "birthYear" = "Birth Year"))

write_csv(info_actors, file.path("gen", "data-preparation", "temp", "info_actors.csv"))