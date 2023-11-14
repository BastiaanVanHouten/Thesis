library(readr)
library(dplyr)

thanos <- read.csv("../../../gen/data-preparation/output/thanos_endgame.csv")


# Changing runtime in numeric
thanos$imdb.com_runtime <- as.numeric(gsub(" min", "", thanos$imdb.com_runtime))





thanos$mpaa_numeric <- as.numeric(factor(thanos$imdb.com_MPAArating,
                                         levels = c("G", "PG", "PG-13", "R"),
                                         labels = c(1, 2, 3, 4)))

thanos$imdb.com_metascore <- as.numeric(thanos$imdb.com_metascore)

write.csv(thanos, "../../../gen/data-preparation/output/thanos_endgame_done.csv")

