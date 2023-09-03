
library(tidyr)

sample_info_actors <- info_actors %>% sample_n(5000, replace = FALSE)


# Assuming your dataset is named "your_dataset" and the column is "Primary Name"
sample_info_actors <- sample_info_actors %>%
    separate("primaryName", into = c("First Name", "Last Name"), sep = "\\s(?=[A-Z])", extra = "merge", remove = FALSE)

# save dataset
write_csv(sample_info_actors, paste0('data/', "sample_info_actors.csv"))

# Assuming your dataset is named "file"
filtered_dataset <- file %>%
    filter(`GreaterEuropean,WestEuropean,Hispanic` >= 0.5)


filtered_dataset_african <- file %>%
    filter(`GreaterAfrican,Africans` >= 0.5 |
             `GreaterAfrican,Muslim` >= 0.5)



install.packages("rethnicity")

