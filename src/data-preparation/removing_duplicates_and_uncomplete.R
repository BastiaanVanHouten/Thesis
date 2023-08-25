# Assuming main_base is your dataset
# Count observations with no NAs or zeros
valid_observations <- main_base[complete.cases(main_base) & !apply(main_base == 0, 1, all), ]
num_valid_observations <- nrow(valid_observations)

# Print the number of valid observations
print(num_valid_observations)
