library(dplyr)


filtered_2018_2019_master <- MASTER_2000_2020.csv %>%
    filter(imdb.com_year == "2018" | imdb.com_year == "2019")


# Replace "path/to/save/csv/file.csv" with the actual path where you want to save the CSV file
write.csv(filtered_2018_2019_master, file = "filtered_2018_2019_master.csv", row.names = FALSE)

cast_2018_2019 <- read_csv("data/scraped/movie_cast_2018_2019.csv")
cast_main_base <- read_csv("data/scraped/cast_main_base.csv") 
cast_not_done <- read_csv("data/scraped/movie_cast_not_done.csv")

cast <- rbind(cast_main_base, cast_2018_2019, cast_not_done)

write.csv(cast, file = "gen/data-preparation/temp/cast.csv", row.names = FALSE)


# filtering for cast without url and in Master
filtered_cast <- cast %>%
    filter(
        `Movie ID` %in% MASTER_2000_2020.csv$imdb.com_imdbid,
        `Profile Picture` != "https://image.tmdb.org/t/p/w500None"
    )

write.csv(filtered_cast, file = "gen/data-preparation/temp/url_in_master_cast.csv")

