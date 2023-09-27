# Check the data types and identify non-numeric values
str(filtered_final_dataset_budget)        


filtered_final_dataset_budget <- filtered_final_dataset %>%
    mutate(
        budget = as.numeric(gsub("\\$", "", budget)),
        boxofficemojo.com_budget = as.numeric(gsub("[^0-9.]", "", boxofficemojo.com_budget)),
        Budget.x = as.numeric(gsub("\\$", "", Budget.x)), # Remove "$" sign
        Budget.x = ifelse(Budget.x == "Not available" | is.na(Budget.x), 0, Budget.x), # Replace "Not available" and NA with 0
        Budget.y = as.numeric(gsub("\\$", "", Budget.y)),
        total_budget = budget + boxofficemojo.com_budget + Budget.x + Budget.y,
        count_non_missing = rowSums(!is.na(select(., c('budget', 'boxofficemojo.com_budget', 'Budget.x', 'Budget.y')))),
        average_budget = total_budget / count_non_missing
    )


unique(filtered_final_dataset_budget$average_budget)
