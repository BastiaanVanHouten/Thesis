# Filter the cast data frame
filtered_cast <- ethnicity_with_cast %>%
    filter(`Movie ID` %in% filtered_final_dataset_budget$`boxofficemojo.com_imdbid`)

# Filter the filtered_cast data frame for rows where asian is NA
filtered_cast <- filtered_cast %>%
    filter(is.na(asian))

write.csv(filtered_cast , "data/cast_ethnicity/no_ethnicity.csv")
