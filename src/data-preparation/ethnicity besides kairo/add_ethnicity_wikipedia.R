# Read in dataset ethnicity of wikipedia
ethnicity_data <- read_csv("ethnicity_wikipedia_cleaned_vs.csv")





ethnicity_data <- subset(ethnicity_data, Name %in% name_actors$primaryName)

info_actors <- left_join(name_actors, ethnicity_data, by = c("primaryName" = "Name", "birthYear" = "Birth Year"))

write_csv(info_actors, file.path("gen", "data-preparation", "temp", "info_actors.csv"))