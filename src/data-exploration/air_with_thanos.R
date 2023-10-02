library(dplyr)
library(readr)

movies_with_air_condition <- read_csv("../..//movies_with_air_condition.csv")
thanos <- read.csv("../../gen/data-preparation/output/thanos_endgame.csv")


df <- left_join(movies_with_air_condition, thanos, by = c("tt_number" = "imdb.com_imdbid"))

# Create the main regression model
model <- lm(Avg_Rank_Third_Year ~ simpson_index +
              Hispanic_condition_t3 + 
              Asian_condition_t3 +
              Black_condition_t3 +
              Black_condition_with_white_t2 +
              Hispanic_condition_with_white_t2 +
              boxofficemojo.com_openingtheaters + 
              imdb.com_runtime + mpaa_numeric + 
              average_budget + 
              imdb.com_year +
              imdb.com_sequel + 
              imdb.com_spinoff +
              imdb.com_remake +
              imdb.com_basedonbook + 
              imdb.com_basedonbookseries + 
              imdb.com_basedonplay + 
              imdb.com_basedoncomic + 
              imdb.com_basedoncomicbook + 
              imdb.com_basedonnovel + 
              imdb.com_basedonshortstory + 
              Nominee +
              Winner +
              Total_Star_Power+
              Action + Adventure + Comedy + Fantasy + Crime + Drama + Mystery + Thriller +
              Romance + Sci.Fi + Biography + Sport + War + Family + Musical + History +
              Horror + Music + Documentary + Western, # Include all genre variables
            data = df)




# print model 
summary(model)


# Create the main regression model
model <- lm(simpson_index ~
              Hispanic_condition_t3 + 
              Asian_condition_t3 +
              Black_condition_t3 +
              Black_condition_with_white_t2 +
              condition_at_least_two_people_t3 +
              condition_at_least_two_people_with_white_t2 +
              Hispanic_condition_with_white_t2 +
              boxofficemojo.com_openingtheaters + 
              imdb.com_runtime + mpaa_numeric + 
              average_budget + 
              imdb.com_year +
              imdb.com_sequel + 
              imdb.com_spinoff +
              imdb.com_remake +
              imdb.com_basedonbook + 
              imdb.com_basedonbookseries + 
              imdb.com_basedonplay + 
              imdb.com_basedoncomic + 
              imdb.com_basedoncomicbook + 
              imdb.com_basedonnovel + 
              imdb.com_basedonshortstory + 
              Nominee +
              Winner +
              the_numbers_com_dirpower_rank +
              Total_Star_Power+
              Action + Adventure + Comedy + Fantasy + Crime + Drama + Mystery + Thriller +
              Romance + Sci.Fi + Biography + Sport + War + Family + Musical + History +
              Horror + Music + Documentary + Western, # Include all genre variables
            data = df)
