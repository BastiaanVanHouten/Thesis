df <- read.csv("../../../gen/data-preparation/temp/final_awards_added.csv")

# Assuming 'df' is your dataset

# Split the 'imdb.com_genres' column into separate elements
genre_list <- strsplit(df$imdb.com_genres, ", ")

# Unlist and extract unique elements
unique_genres <- unique(unlist(genre_list))

# Initialize 20 columns for each genre with default value 0
for (genre in unique_genres) {
  df[[genre]] <- 0
}

# Loop through each row and update the genre columns
for (i in 1:nrow(df)) {
  genres <- unlist(strsplit(df$imdb.com_genres[i], ", "))
  df[i, genres] <- 1
}

write.csv(df, "../../../gen/data-preparation/temp/thanos_not_cleaned.csv")
