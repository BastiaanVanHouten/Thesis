library(dplyr)

master <- read_csv("../../../gen/data-preparation/temp/master.csv")

# Replace "N/A" values in imdb.com_runtime with values from boxofficemojo.com_runtime
master$`imdb.com_runtime` <- ifelse(master$`imdb.com_runtime` == "N/A", master$`boxofficemojo.com_runtime`, master$`imdb.com_runtime`)


# Deselect the specified columns
master <- master %>%
    select( -boxofficemojo.com_budget, 
           -boxofficemojo.com_releasedate, 
           -boxofficemojo.com_imdbid, 
           -boxofficemojo.com_title, 
           -boxofficemojo.com_genres, 
           -imdb.com_plot, 
           -imdb.com_poster, 
           -Budget.x, 
           -Budget.y,
           -total_budget,
           -'MPAA Rating',
           -boxofficemojo.com_runtime,
           -boxofficemojo.com_MPAArating,
           -'Awards and Nominations',
           -'Metacritic Value',
           -'Revenue', 
           -count_non_missing)


# Remove columns 1, 34, and 35 from the master dataset
master <- master %>%
    select(-1, -33, -34)

master_cleaned  <- master %>%
    filter(boxofficemojo.com_openingtheaters >= 50 )


write.csv(master_cleaned, "../../../gen/data-preparation/output/master_cleaned.csv")
