# Load the necessary libraries
library(dplyr)
library(lubridate)
library(readr)

movie_ranks <- read.csv("../../../gen/data-preparation/output/movie_ranks.csv")
thanos <- read.csv("../../../gen/data-preparation/output/thanos.csv")

# Assuming 'Date' is a character or another class
movie_ranks$Date <- as.Date(movie_ranks$Date)


# Assuming 'thanos' is your data frame and 'imdb.com_releasedate' is the column containing the date in the format "24-Jul-19"
# Convert to Date object in the original format
thanos$imdb.com_releasedate <- as.Date(thanos$imdb.com_releasedate, format = "%d-%b-%y")

# Format the Date object to the desired format
thanos$imdb.com_releasedate <- format(thanos$imdb.com_releasedate, "%Y-%d-%m")

write.csv(thanos, "../../../gen/data-preparation/output/thanos.csv")


result <- movie_ranks %>%
    left_join(thanos %>% dplyr::select(imdb.com_imdbid, imdb.com_releasedate), 
              by = c("Movie_ID" = "imdb.com_imdbid"))



result <- result %>%
    mutate(Date = as.Date(Date),
           imdb.com_releasedate = as.Date(imdb.com_releasedate, format = "%Y-%d-%m"))



# Define a time window (e.g., a week)
time_window <- 4  # Number of days



# Calculate the third-year date and one-year date from release_date
result <- result %>%
    mutate(
        third_year_date = imdb.com_releasedate %m+% years(3),
        one_year_date = imdb.com_releasedate %m+% years(1)
    )

# Filter rows where imdb.com_releasedate falls within the time window of Date
releasedate_ranks <- result %>%
    filter(abs(imdb.com_releasedate - Date) <= time_window)

#Remove duplicates 
releasedate_ranks <- releasedate_ranks %>%
    distinct()


# Calculate the average rank for each movie over a one-year period within the third year
result_third_year <- result %>%
  group_by(Movie_ID) %>%
  arrange(Date) %>%
  filter(Date >= third_year_date, Date <= third_year_date + years(1)) %>%
  summarize(Avg_Rank_Third_Year = mean(Rank, na.rm = TRUE))

# Calculate the average rank for each movie over a one-year period within the first year
result_first_year <- result %>%
  group_by(Movie_ID) %>%
  arrange(Date) %>%
  filter(Date >= one_year_date, Date <= one_year_date + years(1)) %>%
  summarize(Avg_Rank_First_Year = mean(Rank, na.rm = TRUE))


# Calculate rank two weeks before release date and summarize
result_two_weeks_before_release <- result %>%
    group_by(Movie_ID) %>%
    arrange(Date) %>%
    filter(Date >= imdb.com_releasedate - weeks(2), Date <= imdb.com_releasedate - weeks(1))

releasedate_ranks <- releasedate_ranks %>%
    left_join(result_first_year, by = "Movie_ID") %>%
    left_join(result_third_year, by = "Movie_ID")


result_with_all_rankings <- releasedate_ranks %>%
    left_join(result_two_weeks_before_release %>%
                  select(Movie_ID, Date_two_weeks_before = Date, rank_two_weeks_before_release = Rank),
              by = "Movie_ID")

#Remove duplicates 
result_with_all_rankings <- result_with_all_rankings %>%
    distinct()

# Rename the Rank column to rank_release
result_with_all_rankings <- result_with_all_rankings %>%
    rename(rank_release = Rank)

# Perform the left join without joining the imdb.com_releasedate column
thanos_endgame <- left_join(thanos, 
                            result_with_all_rankings %>% select(-imdb.com_releasedate), 
                            by = c("imdb.com_imdbid" = "Movie_ID"))

# Remove duplicates from imdb.com_imdbid column
thanos_endgame <- thanos_endgame %>%
    distinct(imdb.com_imdbid, .keep_all = TRUE)

write.csv(thanos_endgame, "../../../gen/data-preparation/output/thanos_endgame.csv")
