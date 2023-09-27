
thanos <- read.csv("../../gen/data-preparation/output/thanos_endgame.csv")




# Define the regression model

# Create the main regression model
model <- lm(Avg_Rank_Third_Year ~ simpson_index + 
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
                imdb.com_basedontvmovie +
                Nominee +
                Winner +
                the_numbers_com_dirpower_rank +
                Total_Star_Power +
                Action + Adventure + Comedy + Fantasy + Crime + Drama + Mystery + Thriller +
                Romance + Sci.Fi + Biography + Sport + War + Family + Musical + History +
                Horror + Music + Documentary + Western, # Include all genre variables
            data = thanos)



# print model 
summary(model)



# Subset your data based on your criteria
subset_data <- thanos%>%
    filter(imdb.com_year > 2016)

# Create the regression model with dummy variables using the subsetted data
model_after_2016 <- lm(Avg_Rank_Third_Year ~ simpson_index + 
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
                imdb.com_basedontvmovie +
                Nominee +
                Winner +
                the_numbers_com_dirpower_rank +
                Total_Star_Power - 1 +
                Action + Adventure + Comedy + Fantasy + Crime + Drama + Mystery + Thriller +
                Romance + Sci.Fi + Biography + Sport + War + Family + Musical + History +
                Horror + Music + Documentary + Western, # Include all genre variables
            data = subset_data)

# Print model summary
summary(model_after_2016)


# Subset your data based on your criteria
subset_data_bef_2016 <- thanos%>%
    filter(imdb.com_year <= 2016)

# Create the regression model with dummy variables using the subsetted data
model_before_2016 <- lm(Avg_Rank_Third_Year ~ simpson_index + 
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
                           imdb.com_basedontvmovie +
                           Nominee +
                           Winner +
                           the_numbers_com_dirpower_rank +
                           Total_Star_Power - 1 +
                           Action + Adventure + Comedy + Fantasy + Crime + Drama + Mystery + Thriller +
                           Romance + Sci.Fi + Biography + Sport + War + Family + Musical + History +
                           Horror + Music + Documentary + Western, # Include all genre variables
                       data = subset_data_bef_2016 )

# Print model summary
summary(model_before_2016)


# Model first year
model_rank_first_year <- lm(Avg_Rank_First_Year ~ simpson_index + 
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
                                imdb.com_basedontvmovie +
                                Nominee +
                                Winner +
                                the_numbers_com_dirpower_rank +
                                Total_Star_Power - 1 +
                                Action + Adventure + Comedy + Fantasy + Crime + Drama + Mystery + Thriller +
                                Romance + Sci.Fi + Biography + Sport + War + Family + Musical + History +
                                Horror + Music + Documentary + Western- 1, # Include all genre variables
                            data = thanos)

summary(model_rank_first_year)

# model release date
model_release_date <- lm(rank_release~ simpson_index + 
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
                                imdb.com_basedontvmovie +
                                Nominee +
                                Winner +
                                the_numbers_com_dirpower_rank +
                                Total_Star_Power - 1 +
                                Action + Adventure + Comedy + Fantasy + Crime + Drama + Mystery + Thriller +
                                Romance + Sci.Fi + Biography + Sport + War + Family + Musical + History +
                                Horror + Music + Documentary + Western, # Include all genre variables
                            data = thanos)

summary(model_release_date)
