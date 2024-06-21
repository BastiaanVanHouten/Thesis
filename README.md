# Thesis
The repository for my thesis. I saved the large files into my local repository. 


Research Methodology study 1

This study aims to investigate the relationship between Racial Authentic Inclusive 
Representation and Long-term Audience Engagement in Hollywood films. The following 
sections will provide a detailed overview of the data collection and sampling procedures, as 
well as a clear operationalization of the variables. Given the subjective nature of Racial 
Authentic Inclusive Representation, the Bechdel Test was employed as a quantitative measure 
for this concept. Notably, it will be discussed across three distinct levels, as defined by the 
Bechdel test, elaborated in the operationalization section.

Main data sources

The main data sources for this study are the Internet Movie Database (IMDb), The Numbers, 
and The Movie Database (TMDB). IMDB is the most important source, as it will be used to 
measure Long-term Audience Engagement. While IMDb users and the general filmgoing 
population differ somewhat in demographics, previous research has used IMDB data numerous 
times demonstrating the capability of using it for the broader filmgoing audience (e.g. Ghiassi
et al., 2017; Partha et al., 2019; Apala et al., 2013).

Sample

The films for the sample were chosen carefully and based on specific criteria. IMDB started in 
1996 but was not widely used until 2003 so the sample was limited to films released after the 
year 2000 (for a further explanation, see the dependent variable operationalization). 
Films produced outside the United States and animated films were also filtered out, because 
Hollywood is the focus of this study and voice actors are not represented on screen, 
undermining representation. Following Joshi and Mao (2012), the analysis only included films 
that received a wide release, requiring a minimum of 500 screens at their launch. 
To measure Racial Authentic Inclusive Representation, data on interactions between actors is 
required (for a further explanation, see Racial Authentic Inclusive Representation variable 
operationalization). Observations with missing data which appeared to be random were 
eliminated. After applying all criteria, the sample consisted of 1,178 films. 

Variable operationalization

Long-term Audience Engagement (Dependent Variable)
Long-term Audience Engagement was operationalized using IMDb's MovieMeter, a metric 
derived from popularity rankings. A score of one means that the film was the most popular with 
regards to clicks, page views and reviews on IMDB in that week compared to other films. 
Therefore, this film score includes direct indicators of Long-term Audience Engagement, such 
as online discussions, reviews, and word-of-mouth conversations. To measure sustained 
engagement, I measured Long-term Audience Engagement as the average ranking of a film 
over a one-year period, starting in the third year after its release. I chose this metric because it 
shows how engaged audiences are with a film after a few years, and the average reduces the 
influence of any spikes or certain drops in the engagement of audiences with a film. 

Ethnicity

To determine actors’ ethnicity, I used the Kairos API, a deep learning algorithm that can detect 
ethnicity through facial recognition. I collected the profile pictures of the actors and actresses 
with a scraper from IMDb and processed these with the API. The Kairos API is chosen because 
of its efficiency, accuracy (99.63%), and ability to handle a large dataset (Kairos, 2023). In the 
films included in the sample of this study a total of 62,834 characters were present. This count 
includes instances where an actor or actress appeared in multiple films. It also included 
uncredited people (7,251). The Kairos API analyzed 26,891 images found on IMDb of the total 
of 32,513 unique actors and actresses. 

For the remaining imageless people the ethnicities were based on their first and last name using 
the R package Rethnicity, which has an accuracy of around 80%. People not having an image 
on IMDB is correlated with not having played a significant role in a film 3. Therefore, they are assumed to be less important for the analysis.

Racial Authentic Inclusive Representation (Independent Variables) 

Quantifying the concept of Racial Authentic Inclusive Representation in films has resulted in 
researchers using the Bechdel-Wallace test (1985), originally designed to measure
representation of women in a film (Agarwal, 2015). The Bechdel test is chosen as a tool for 
measuring Racial Authentic Inclusive Representation in films because of its adaptability to this 
study’s specific focus (Lazar et al., 2020), its potential for automation, and its quantifiability 
(Argarwal, 2015). The original Bechdel test is structured around three levels, (T1) The movie 
has to have at least two named women in it (T2) who talk to each other, (T3) about something 
other than a man (Bechdel-Wallace, 1985)

Building on this foundation, the Bechdel test was adapted, drawing inspiration from Lazar et 
al. (2020). The measurement of Racial Authentic Inclusive Representation for the three distinct 
minority ethnicities in this study allows for an examination of the concept across three distinct 
levels (T1, T2, T3):
 (T1) Two named {ethnicity} characters appear in film X.
 (T2) Two named {ethnicity} characters appear in a scene together.
 (T3) Two named {ethnicity} characters appear in a scene together without a white character. 

As can be seen the modified Bechdel test similar to the original requires the actors to be named. 
Therefore, the first step of conducting the modified Bechdel test was to create a process which 
removed ‘generic’ characters from the dataset. To filter generic characters from the dataset, I 
identified frequently occurring tokens, where a token is a segment of a name divided by spaces. 
I then removed characters which only included tokens within a stop word list. The stop word 
list eventually contained 915 words, such as "doctor," "agent," and "the." The entire list can be 
seen in Appendix A. 

I made an exception to the character filter: I did not remove a character if the stop word was the 
first token in their name for example "Colonel Rich Bron" and “Doctor Johnson” were
characters kept. However, the addition to this exception was when the first token was the only 
token. For instance, a character such as "Colonel" would be removed.
To delve deeper into Authentic and Inclusive characters I implemented steps 2 and 3 of the 
modified Bechdel test. Previous research such as Argawal (2015) used screenplays to conduct 
the Bechdel test. However, film scripts can be changed during production, so they may not 
match the final film. Therefore, I decided to take a different approach and use subtitles for the 
hearing impaired. Subtitles represent the final version of the film's dialogue, capturing it exactly 
as it appears in the film. 

By using the subtitles.org API I was able to find subtitles for the hearing impaired in a format 
that could be standardized for testing. Each subtitle file was in an a strict formatted .srt file, 
which has a unique identifier, precise start and end times, and one or two lines of text. As 
illustration, the opening of the film "300: Rise of an Empire": 
           1
00:00:38,363 --> 00:00:40,698
(HORSE NICKERS)
           2
00:01:02,654 --> 00:01:07,024
QUEEN GORGO: The oracle's
words stand as a warning.
           3
00:01:07,026 --> 00:01:08,225
A prophecy.
           4
00:01:08,227 --> 00:01:11,796
"Sparta will fall.
          20

In these subtitle files, when it is unclear who is speaking, the person is identified and labeled 
("QUEEN GORGO"). To ascertain the individuals in the scenes, I employed the 
en_core_web_md model from the spaCy Natural Language package, which can recognize 
entities in the text. To identify scenes, I wrote code which went through the subtitle file and 
looked for pauses in dialogue. If a pause exceeded five seconds, the code identified it as a new 
scene. I chose five seconds because it allows the audience to mentally adjust to the new scene 
without disrupting the narrative flow. Because this is a threshold, even if a scene switch took 
longer, it would still count it as one scene switch. Finally, I conducted a fuzzy merge, aligning 
the people mentioned list with their respective ethnicities within the dataset.
After processing the subtitles, the dataset comprised scene indices, speakers, individuals 
mentioned, and the ethnicities of the characters. The subsequent step involved applying the 
revised Bechdel Test to this dataset. Films were classified based on whether they satisfied the 
conditions (T1), (T2) and (T3) for different ethnicities. Films which hold the condition T3 
directly hold the other conditions as well. These classification served as the independent 
variables utilized in the regression models. 

Covariates

It is important to account for additional factors that have been identified as influencing a film’s 
success, in doing so this study draws upon previous research. By controlling for the impact of 
these variables, more accurate estimations can be derived for the variables under investigation. 
Moreover, by including these covariates the chances for an omitted variable bias is reduced.
The variables considered alongside Racial Authentic Inclusive Representation in this study 
include Sequel, the star power of both Actors and Directors, MPAA rating, Number of Opening 
Screens, Critical Acclaim, Awards, Production Budget, Genre, Source and Seasonality. Table 
1 provides detailed information including which sources identified which variables, the 
following paragraphs briefly discuss how the variables are measured in this study. 
The measure for STARPOWERi is based on the measurement from Nelson and Glotfelty 
(2012), it is the four highest-grossing actors' ranking on the website The Numbers for one year 
before the film. For DIRECTORPOWERi the directors' ranking on The Numbers is also used,
also the year before the film. 

With regards to critical acclaim, the CRITICSi value is the average rating on metacritic.com. 
Moreover, this research will use the actual number of awards NOMINATIONSi as a proxy for 
award nomination. WINSi will also be added to the model to represent awards wins. Because 
there is an abundance of available film awards this study uses the awards mentioned on the 
website of IMDB which makes it very easy and accessible to account for a vast amount of 
awards internationally and nationally. 

MPAAi rating is given by the Motion Picture Association of America and is used to rate a film's 
suitability for certain audiences based on its content. These ratings are encoded as an interval 
variable as [0 = unrated; 1 = G; 2 = PG; 3 = PG-13; 4 = R;5 = C-17]. SCREENSi is the amount 
of opening theater screens the film had according to the Numbers. BUDGETi was the 
production budget available at one of the three data sources used (IMDB, The Numbers and 
TMDB), if multiple production budgets were available across the sources the average was 
taken. In this study, SEQUELi indicates where the film is a sequel. It is a dummy variable, 
which takes the value one if the film is a sequel. 

Moreover, this study introduced 19 genres through dummy variables: Action, Adventure, 
Comedy, Crime, Drama, Family, Fantasy, Horror, Romance, Musical, Sci-Fi, Mystery, Thriller, 
Western, Biography, Documentary, History, Music, Sport and War. Because a film could have 
multiple genres, these dummy variables are not mutually exclusive. 
Within this study the four seasons (SPRINGi, SUMMERi, FALLi, WINTERi) are encoded as 
the following. Spring[March, April, May] Summer [June, July, August] Fall [September, 
October, November], Winter [December, January, February]. RUNTIMEi is included as the 
actual numerical value in minutes, following.

Furthermore, following Hofmann, Clement, Völckner, and Hennig-Thurau (2016), multiple 
dummy variables were added to control for whether the film was {BASED ON}i a book, comic, 
novel, short story, or TV series. Moreover, whether the film is a REMAKEi or SPINOFFi .
Similar, to variables representing the genres of the film, these based on dummy variables are 
not mutually exclusive because a film could be based on multiple sources. In order to account 
for potential variations over time, dummy variables YEARi were introduced for each year 
within the sample, enhancing the model's ability to control for temporal effects.

Models study 1

Following the approach outlined by Clement, Wu, and Fischer (2014), this research uses a loglog regression model. As such, all variables that are not dummy variables were log-transformed. 
However, it is worth noting that numerous continuous variables had zero values, and taking the 
logarithm of '0' would result in an error. To address this, a small constant value of '1’ was added 
to all variables which were continuous before taking the logarithm, ensuring meaningful results. 
For the variables director power and star power which were numbers between 0 and 1.5 the 
value was first multiplied by one hundred before the number was added, assuring the small 
integer added did not have too much effect on the value. Because Racial Authentic Inclusive 
Representation provides different levels, models were made for all three levels with the 
ethnicity conditions as independent variables. 

Model T1 :
log(LTAEi) = β0 + β1 × ASIANT1i + β2 × BLACKT1i + 
β3 × HISPANICT1i + β4 × log(DIRECTORPOWERi) +
β5 × log(CRITICi) + β6 × log(NOMINATIONSi) + β7 × log(WINSi) +
β8 × log(MPAAi) + β9 × log(SCREENSi) + β10 × log(BUDGETi) +
β11 × ACTIONi + β12 × ADVENTUREi + β13 × ANIMATIONi +
β14 × COMEDYi + β15 × CRIMEi + β16 × DRAMAi + β17 × FAMILYi +
β18 × FANTASYi + β19 × HORRORi + β20 × MUSICALi +
β21 × MYSTERYi + β22 × ROMANCEi + β23 × SCI-FIi +
β24 × THRILLERi + β25 × WESTERNi + β26 × BIOGRAPHYi +
β27 × DOCUMENTARYi + β28 × MUSICi + β29 × HISTORYi +
β30 × SPORTi + β31 × SPRINGi + β32 × SUMMERi +
β33 × AUTUMNi + β34 × WINTERi + β35 × log(RUNTIMEi) +
β36 × BOOKi + β37 × COMICi + β38 × NOVELi + β39 × SHORTSTORi +
β40 x TVSERIESi + β41 x REMAKEi + β42 x SPINOFFi + β43 x SERIESi +
β44 × log(STARPOWERi) + β45 ×YEAR2000i + β46 × YEAR2001i + β47 × YEAR2002i + 
β48 x YEAR2003i + β49 × YEAR2004i + β50 × YEAR2005i + β51 × YEAR2006i + 
β52 × YEAR2007i + β53 × YEAR2008i + β54 × YEAR2009i + β55 × YEAR2010i + 
β56 × YEAR2011i + β57 × YEAR2012i + β58 × YEAR2013i + β59 × YEAR2014i +
β60 × YEAR2015i + β61 × YEAR2016i + β62 × YEAR2017i + β63 × YEAR2018i + β64 × YEAR2019i + εi

Model T2:

log(LTAEi) = β0 + β1 × ASIANT2i + β2 × BLACKT2i + β3 × HISPANICT2i + 
β4 × log(DIRECTORPOWERi) + … β60 × YEAR2015i + β61 × YEAR2016i + β62 × YEAR2017i + β63 × 
YEAR2018i + β64 × YEAR2019i + εi
Model T3: 

log(LTAEi) = β0 + β1 × ASIANT3i + β2 × BLACKT3i + β3 × HISPANICT3i + 
β4 × log(DIRECTORPOWERi) + … β60 × YEAR2015i + β61 × YEAR2016i + β62 × YEAR2017i + β63 × 
YEAR2018i + β64 × YEAR2019i + εi

In these models, LTAEi represents the Long-term Audience Engagement for film i. ASIANT , 
BLACKT and HISPANICT represent the Authenticity and Inclusiveness, identification, of 
Hispanic, Black, and Asian representation in film i. The other variables are the control variables. 

Research Methodology 2

The research methodology of Study 2 closely mirrors that of Study 1. As previously mentioned, 
the #OscarsSoWhite movement was selected as a reference point for this study. To capture the 
temporal dynamics, a step dummy variable, After_Jan_2015, was generated. Films released in 
or after 2015 were assigned a value of one, indicating the period when Racial Representation 
gained heightened cultural significance. The assumption, supported by continued emphasis on 
belonging and community in 2020 (Neufeld, 2020), and findings by Lazar et al. (2021), is that 
this period of cultural significance extended at least from 2015 to 2019. This assumption 
obviated the necessity to explicitly model a moment when Racial Representation ceased to be 
a prominent cultural topic.

Models

To investigate the potential moderating effect of an external factor on the relationship between 
Racial Authentic Inclusive Representation and Long-term Audience Engagement the 
interaction term after_jan_2015 was incorporated into the three T1, T2, and T3 models. For 
example, the T1 model: 

log(LTAEi) = β0 + β1 × ASIANT1i + β2 × BLACKT1i + β3 × HISPANICT1i + β4 
×FILMSAFTERJAN2015i* ASIANT1i + β5×FILMSAFTERJAN2015i* BLACKT1i + β6 × 
FILMSAFTERJAN2015i * HISPANICT1i + {Control Variables} + εi

In this model, LTAE similar to the previous study represents the Long-term Audience 
Engagement for film i, FILMSAFTERJAN2015 is a dummy variable that takes a value of 1 if 
the film was released in or after February 2015. The interaction terms FILMSAFTERJAN2015i
× ASIANT1i, FILMSAFTERJAN2015i * BLACKT1i and FILMSAFTERJAN2015i * 
HISPANICT1i allow to capture whether the effect of Racial Authentic Inclusive Representation 
on Long-term Audience Engagement differs before and after January 2015.

What needs to be noted is that while the interaction terms are included in the model, the main 
effect of the dummy variable of after January 2015 is not included. This is because it would 
have multicollinearity issues with the year dummies incorporated as control variables.
