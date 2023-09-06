master_2000_2020 <- MASTER_2000_2020 %>%
    filter(boxofficemojo.com_imdbid %in% main_base$imdb_id)

na_observation_count <- sum(rowSums(is.na(master_2000_2020)) > 0)


main_base_no_NA <- main_base_updated %>%
    filter(budget != 0)


main_base_updated <- main_base %>%
    mutate(budget = ifelse(budget == 0, 
                           MASTER_2000_2020$boxofficemojo.com_budget[main_base$common_id], 
                           budget))

main_base_no_NA <- main_base %>%
    filter(budget != 0)

master_2000_2020_no_NA <- MASTER_2000_2020 %>%
    filter(complete.cases(.))


master_2000_2020_1998_2017 <- MASTER_2000_2020 %>%
    filter(complete.cases(.))