# Load the necessary libraries
library(dplyr)
library(lubridate)
library(readr)



# Assuming 'Date' is a character or another class
movie_ranks$Date <- as.Date(movie_ranks$Date)

movie_ranks <- read_csv("Master/Thesis/movie_ranks.csv", 
                        col_types = cols(Date = col_date(format = "%Y-%m-%d")))
View(movie_ranks)


# Assuming master_with_simpson is your dataset and Date is the column you want to convert
master_with_simpson <- master_with_simpson %>%
  mutate(imdb.com_releasedate = dmy(imdb.com_releasedate))



result <- movie_ranks %>%
  left_join(master_with_simpson %>% select(imdb.com_imdbid, imdb.com_releasedate), 
            by = c("Movie_ID" = "imdb.com_imdbid"))


result <- result %>%
  mutate(Date = as.Date(Date),
         imdb.com_releasedate = as.Date(imdb.com_releasedate))



# Define a time window (e.g., a week)
time_window <- 4  # Number of days

# Filter rows where imdb.com_releasedate falls within the time window of Date
releasedate_ranks <- result %>%
  filter(abs(imdb.com_releasedate - Date) <= time_window)


# Calculate release year from imdb.com_releasedate
result <- result %>%
  mutate(
    release_year = year(imdb.com_releasedate),
    recorded_year = year(Date)
  )


# Calculate the third-year date from release_date
result <- result %>%
  mutate(
    third_year_date = imdb.com_releasedate %m+% years(3)
  )

# Calculate the average rank for each movie over a one-year period
result <- result %>%
  group_by(Movie_ID) %>%
  arrange(Date) %>%
  filter(Date >= third_year_date, Date <= third_year_date + years(1)) %>%
  summarize(Avg_Rank_Third_Year = mean(Rank, na.rm = TRUE))

# Calculate the third-year date and one-year date from release_date
result <- result %>%
  mutate(
    third_year_date = imdb.com_releasedate %m+% years(3),
    one_year_date = imdb.com_releasedate %m+% years(1)
  )

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

# Calculate rank within the week of release date
result_week_of_release <- result %>%
  group_by(Movie_ID) %>%
  arrange(Date) %>%
  filter(Date >= imdb.com_releasedate, Date <= imdb.com_releasedate + weeks(1))

# Calculate rank one week before release date
result_one_week_before_release <- result %>%
  group_by(Movie_ID) %>%
  arrange(Date) %>%
  filter(Date >= imdb.com_releasedate - weeks(1), Date <= imdb.com_releasedate)


average_first_year_rank <- mean(result_first_year$Avg_Rank_First_Year, na.rm = TRUE)
average_third_year_rank <- mean(result_third_year$Avg_Rank_Third_Year, na.rm = TRUE)

final_with_ranks <- left_join(master_with_simpson, result_third_year , by = c("imdb.com_imdbid" = "Movie_ID"))
