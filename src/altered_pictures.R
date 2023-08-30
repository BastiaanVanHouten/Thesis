library(dplyr)

MASTER_2000_2020 <- MASTER_2000_2020 %>%
    filter(imdb.com_imdbid %in% main_base$imdb_id)


only_pictures_cast <- movie_cast_1_ %>%
    select(`Profile Picture`, 'Cast Member Name', actor_imdb_id)%>%
    filter(`Profile Picture` != "https://image.tmdb.org/t/p/w500None")


# Save the filtered and selected data frame to a CSV file
write.csv(only_pictures_cast, file = "only_pictures_cast.csv", row.names = FALSE)


zero_count <- sum(movie_budget_revenue_sequal$Budget == 0)
print(zero_count)
