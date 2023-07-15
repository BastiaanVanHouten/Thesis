DATA=../../data
TEMP=../../gen/data-preparation/temp
DP=../../src/data-preparation
OUTPUT=../../gen/data-preparation/output

all: $(DATA)/basics.csv.gz $(DATA)director.csv.gz $(DATA)name.basics.csv.gz $(DATA)principals.csv.gz $(TEMP)actors.csv $(TEMP)directors.csv $(TEMP)info_actors.csv $(TEMP)us_production_movies_cleaned.csv


$(TEMP)actors.csv: 

$(TEMP)directors.csv: 

$(TEMP)info_actors.csv:$(DP)/create_dataset_info_actors 

$(TEMP)us_production_movies_cleaned.csv: $(DP)/create_main_base.R 
		R --vanilla < $(DP)/calendar_datasets.R 

$(DATA)/basics.csv.gz $(DATA)director.csv.gz $(DATA)name.basics.csv.gz $(DATA)principals.csv.gz: $(DP)/download_data.R 
		R --vanilla < $(DP)/download_data.R 

$(DP)/install_packages.R: $(DP)/install_packages.R
		R --vanilla < $(DP)/install.packages.R