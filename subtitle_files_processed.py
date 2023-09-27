
from subtitle_dataframes_io import *
from collections import Counter
from datetime import datetime, date, timedelta
import spacy
from collections import defaultdict
import os
import pysrt
from dataclasses import dataclass
import pandas as pd
​
# Define the SpaCy model and load it
nlp = spacy.load("en_core_web_md")
​
# Initialize a counter for processed files
files_processed = 0
​
# List all files in the folder
folder_path = '../../subtitles'
output_folder = '../../subtitle_csv'  # New folder for CSV files
os.makedirs(output_folder, exist_ok=True)
# List all files in the folder
files = os.listdir(folder_path)
​
@dataclass()
class FuzzyMerge:
    left: pd.DataFrame
    right: pd.DataFrame
    left_on: str
    right_on: str
    how: str = "inner"
    cutoff: float = 0.6
​
    def main(self) -> pd.DataFrame:
        temp = self.right.copy()
        temp[self.left_on] = [
            self.get_closest_match(x, self.left[self.left_on]) for x in temp[self.right_on]
        ]
        return self.left.merge(temp, on=self.left_on, how=self.how)
​
    def get_closest_match(self, left: pd.Series, right: pd.Series) -> str or None:
        matches = get_close_matches(left, right, cutoff=self.cutoff)
        return matches[0] if matches else None
​
# For identifying people
people_blacklist = ['Jesus', 'Jesus Christ', 'Whoo', 'God', 'Mm', 'Dude', 'Mm-hmm', 'Huh']
# Define the list of generic entities
generic_entities = [
    'Mom', 'Dad', 'Grandma', 'Grandpa', 'Sister', 'Brother', 'Aunt', 'Uncle', 'Cousin',
    'Child', 'Parent', 'Spouse', 'Friend', 'Teacher', 'Doctor', 'Boss', 'Neighbor',
    'Stranger', 'Police', 'Coach', 'Waiter', 'Waitress', 'Chef', 'Bartender', 'Driver',
    'Detective', 'Nurse', 'Lawyer', 'Journalist', 'Soldier', 'Scientist'
]
​
for file_name in files:
    if files_processed >= 1000:
        break
​
    if file_name.endswith('.srt'):
        print(f"Processing file: {file_name}")
        file_path = os.path.join(folder_path, file_name)
​
        # Load and process the subtitle file using your script
        subs = pysrt.open(file_path)
        subtitle_df = generate_base_subtitle_df(subs)  # You need to implement this function
        subtitle_df = generate_subtitle_features(subtitle_df)  # You need to implement this function
        subtitle_df['cleaned_text'] = subtitle_df['concat_sep_text'].map(clean_line)  # You need to implement clean_line
        sentences = partition_sentences(remove_blanks(subtitle_df['cleaned_text'].tolist()), nlp)  # You need to implement partition_sentences
        
​
        # Check if all values in the 'speaker' column are NA's
        if subtitle_df['speaker'].isna().all():
            print(f"Skipping file: {file_name} as all values in the 'speaker' column are NA's.")
            continue  # Skip processing this file and move to the next one
​
        
        x = 1 
        delay_threshold = timedelta(seconds=5)
        scene_index = 1  # Initialize scene index
        scene_labels = {}  # Dictionary to store scene labels
​
​
        while x < len(subtitle_df):
            if subtitle_df.iloc[x].cleaned_text or subtitle_df.iloc[x].laugh == 1:
                y = 1
​
            while not subtitle_df.iloc[x - y].cleaned_text and subtitle_df.iloc[x - y].laugh == 0:
                y += 1
            delay = datetime.combine(date.today(), subtitle_df.iloc[x].start_time) - datetime.combine(date.today(), subtitle_df.iloc[x - y].end_time)
​
            if delay > delay_threshold:
            # Add scene information to subtitle_df
                subtitle_df.at[x, 'scene_index'] = scene_index
​
​
            # Increment scene index and update scene label if necessary
                scene_index += 1
                if delay > timedelta(minutes=5):
                    scene_labels[scene_index] = f'Scene {scene_index} (Long Pause)'
​
            x += 1
​
        # Check if 'scene_index' exists in the DataFrame
        if 'scene_index' in subtitle_df.columns:
            subtitle_df['scene_index'].fillna(method='ffill', inplace=True)
        else:
            print(f"The 'scene_index' column does not exist in the DataFrame for file: {file_name}")
​
        # Process entities and mentions as you described in your original code
        people_mention_dict = defaultdict(list)
        sentences = partition_sentences(remove_blanks(subtitle_df['cleaned_text'].tolist()), nlp)
        doc = nlp(' '.join(sentences))
        
​
        for ent in doc.ents:
            if ent.label_ == 'PERSON' and ent.text not in people_blacklist:
                try:
                    cleaned_text_index = sentences.index(ent.sent.text)
                    people_mention_dict[ent.text].append(cleaned_text_index)
                except ValueError:
                    continue  # Skip processing this entity and continue with the next
​
        for token in doc:
            token_text = token.text.strip()
            if token_text in generic_entities and token_text not in people_blacklist:
                try:
                    cleaned_text_index = sentences.index(token.sent.text)
                    people_mention_dict[token_text].append(cleaned_text_index)
                except ValueError:
                    print(f"Text not found in sentences: {token.sent.text}")
                    continue  # Skip processing this token and continue with the next
​
        result_data = {'Sentence': [], 'Mentioned Entities': []}
        result_df = pd.DataFrame(result_data)
​
        dfs_to_concatenate = []
​
        for entity, mention_indices in people_mention_dict.items():
            for index in mention_indices:
                # Create a DataFrame for each row
                df_to_append = pd.DataFrame({'Sentence': [sentences[index]], 'Mentioned Entities': [entity]})
                dfs_to_concatenate.append(df_to_append)
​
        # Concatenate all the DataFrames in the list
        result_df = pd.concat(dfs_to_concatenate, ignore_index=True)
​
        # Convert the "cleaned_text" column in subtitle_df to string data type
        subtitle_df['cleaned_text'] = subtitle_df['cleaned_text'].astype(str)
​
        # Convert the "Sentence" column in result_df to string data type
        result_df['Sentence'] = result_df['Sentence'].astype(str)
​
        # Merge the DataFrames
        merged_df = FuzzyMerge(left=subtitle_df, right=result_df, left_on="cleaned_text", right_on="Sentence", how="left").main()
​
        # Remove duplicates from the merged DataFrame
        merged_df.drop_duplicates(subset=['cleaned_text'], inplace=True)
​
        # Save the merged DataFrame to a CSV file
        output_file_name = f"{os.path.splitext(file_name)[0]}.csv"
        output_file_path = os.path.join(output_folder, output_file_name)
        merged_df.to_csv(output_file_path, index=False)
​
​
Processing file: (2015)BlackMass[ING].srt
Skipping file: (2015)BlackMass[ING].srt as all values in the 'speaker' column are NA's.
Processing file: 01 - 2000 Coyote Ugly - [ENGLISH] Hearing Impaired By Ammar Schwarzenegger.srt
Skipping file: 01 - 2000 Coyote Ugly - [ENGLISH] Hearing Impaired By Ammar Schwarzenegger.srt as all values in the 'speaker' column are NA's.
Processing file: 05 The Omen Uncut ReBoot - Horror 2006 English.srt
Skipping file: 05 The Omen Uncut ReBoot - Horror 2006 English.srt as all values in the 'speaker' column are NA's.
Processing file: 102.Dalmatians.2000.1080p.WEBRip.DD5.1.x264-NTb.srt
Processing file: 1080p.BluRay.x264.srt
Processing file: 1080p.WEBRip.x264-[YTS.srt
Skipping file: 1080p.WEBRip.x264-[YTS.srt as all values in the 'speaker' column are NA's.
Processing file: 10_000 B.C 1080p by Bokutox of www.yify-torrents.srt
Skipping file: 10_000 B.C 1080p by Bokutox of www.yify-torrents.srt as all values in the 'speaker' column are NA's.
Processing file: 13 Going On 30 (2004) [1080p] [YTS.srt
Processing file: 1408 (2007).srt
Skipping file: 1408 (2007).srt as all values in the 'speaker' column are NA's.
Processing file: 15.Minutes.2001.1080p.Blu-ray.Remux.AVC.DTS-HD.MA.5.1-KRaLiMaRKo.srt
Processing file: 16.Blocks.2006.720p.BluRay.x264.vice-hi.srt
Processing file: 17.Again.2009.BRRip.AC3.XviD-LTRG.srt
Processing file: 2 Guns [2013] HDRip XViD [AC3]-ETRG.srt
Processing file: 20-The World Is Not Enough.[1999].720pDVDRIP.XVID.srt
Skipping file: 20-The World Is Not Enough.[1999].720pDVDRIP.XVID.srt as all values in the 'speaker' column are NA's.
Processing file: 2004-01-24--darkness falls_720p [bluray.x264].srt
Processing file: 2006.Dave Chappelles Block Party.srt
Processing file: 2012.[2009].DVDRIP.XVID.[Eng]-DUQA.srt
Processing file: 21.and.Over.2013.720p.BluRay.x264.DTS-HDWinG.srt
Processing file: 21.Jump.Street.2012.720p.x264.DTS-HDChina.english.srt
Skipping file: 21.Jump.Street.2012.720p.x264.DTS-HDChina.english.srt as all values in the 'speaker' column are NA's.
Processing file: 22-Casino Royale.[2006].720pDVDRIP.XVID.srt
Skipping file: 22-Casino Royale.[2006].720pDVDRIP.XVID.srt as all values in the 'speaker' column are NA's.
Processing file: 22.Jump.Street.2014.720p.BluRay.x264-SPARKS.srt
Processing file: 28.Days.2000.WEBRip.x264-ION10.srt
Processing file: 3.Days.to.Kill.2014.EXTENDED.720p.BluRay.x264-SPARKS-HI.srt
Processing file: 3.Strikes.2000.1080p.WEBRip.x264-RARBG.en.srt
Processing file: 30.Days.Of.Night.2007.1080p.BrRip.x264.YIFY.srt
Skipping file: 30.Days.Of.Night.2007.1080p.BrRip.x264.YIFY.srt as all values in the 'speaker' column are NA's.
Processing file: 30.Minutes.or.Less.2011.HI.srt
Processing file: 300.Rise.Of.An.Empire.2014.1080p.WEB-DL.AAC.2.0.H.264-RARBG-HI.srt
Processing file: 40days40nights eng.srt
Processing file: 47 Ronin 2013 REAL HDRip XviD AC3-AQOS-hi.srt
Processing file: 47.Meters.Down.Uncaged.2019.720p.HDCAM-GETB8-HI.srt
Processing file: 50.50.2011.720p.BRRip.x264.AAC-ViSiON.srt
Processing file: 720p.BluRay.srt
Processing file: 8 Mile.srt
Processing file: 88 Minutes (2007) (Al Pacino) (moviesbyrizzo).srt
Processing file: 90.Minutes.in.Heaven.2015.720p.BluRay.x264-DRONES-HI.srt
Processing file: 911 (2000).srt
Skipping file: 911 (2000).srt as all values in the 'speaker' column are NA's.
Processing file: A Haunted House.[2013].R5.LINE.DVDRIP.DIVX.srt
Skipping file: A Haunted House.[2013].R5.LINE.DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: A Knights Tale (2001) [1080p] [BluRay] [YTS.MX]_HI.srt
Skipping file: A Knights Tale (2001) [1080p] [BluRay] [YTS.MX]_HI.srt as all values in the 'speaker' column are NA's.
Processing file: A Thousand Words.[2012].DVDRIP.DIVX.[Eng]-DUQA.srt
Skipping file: A Thousand Words.[2012].DVDRIP.DIVX.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: A-Copy1.Quiet.Place.2018.720p.BluRay.x264-SPARKS-HI.srt
Processing file: A-X-L.2018.HDRip.XviD.AC3-EVO.srt
Processing file: A.Beautiful.Day.in.the.Neighborhood.2019.1080p.BluRay.x264-DRONES-HI.srt
Processing file: A.Dogs.Journey.2019.1080p.BluRay.x264-GECKOS-HI.srt
Processing file: A.Dogs.Way.Home.2019.720p.HC.HDRip.X264.srt
Processing file: A.Good.Day.To.Die.Hard.2013.EXTENDED.720p.BluRay.DTS-ES.x264-PublicHD.srt
Processing file: A.Good.Year.2006.720p.BluRay.x264.srt
Processing file: A.Haunted.House.2.2014.HDRip.XViD.juggs[ETRG].srt
Processing file: A.I.Artificial.Intelligence.2001.1080p.Bluray.x264.anoXmous_eng.srt
Processing file: A.Lot.Like.Love.2005.1080p.EUR.BluRay.AVC.DTS-HD.MA.5.1-FGT.ENG-HI.srt
Processing file: A.Madea.Family.Funeral.2019.720p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: A.Million.Ways.to.Die.in.the.West.2014.HDRip.X264.AC3.5.1-PLAYNOW-HI.srt
Processing file: A.Nightmare.on.Elm.Street.2010.DVDRip.XVID.AC3-lOVE.srt
Processing file: A.Perfect.Getaway.UNRATED.Directors.Cut.BDRip.XviD-ESPiSE.CD1.SDH.srt
Processing file: A.Perfect.Getaway.UNRATED.Directors.Cut.BDRip.XviD-ESPiSE.CD2.SDH.srt
Processing file: A.Quiet.Place.2018.720p.BluRay.x264-SPARKS-HI.srt
Processing file: A.Simple.Favor.2018.720p.BluRay.X264-DEFLATE-HI.srt
Processing file: A.Star.is.Born.2018.720p.BluRay.DD5.1.X264-iFT-HI.srt
Processing file: A.Very.Harold.And.Kumar.Christmas.2011.720p.BluRay.x264-SPARKS.Hi.srt
Processing file: A.Walk.Among.the.Tombstones.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: A.Wrinkle.in.Time.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: Abandon.2002.720p.WEB-DL.DD5.1.H264-alfaHD.srt
Text not found in sentences: Oh, I understand, Doctor.    
Processing file: Abduction.2011.BluRay.720p.1080p.HI.srt
Processing file: About.A.Boy.2002.720p.BluRay.x264-HD4U.eng.srt
Processing file: About.Last.Night.2014.1080p.BluRay.x264-YIFY.CHI.srt
Skipping file: About.Last.Night.2014.1080p.BluRay.x264-YIFY.CHI.srt as all values in the 'speaker' column are NA's.
Processing file: Abraham.Lincoln.Vampire.Hunter.2012.720p.BluRay.x264.DTS-HDChina.eng.srt
Processing file: Accepted.2006.1080p.BluRay.x264.DTS-FGT.eng.srt
Processing file: Acrimony.2018.1080p.BluRay.srt
Skipping file: Acrimony.2018.1080p.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: Act.of.Valor.2012.PROPER.1080p.BluRay.x264-SPARKS.srt
Processing file: Ad.Astra.2019.1080p.WEB-DL.DD5.1.x264-CMRG-HI.srt
Processing file: Admission.2013.720p.WEBRip.x264.AC3-FooKaS-eng.srt
Processing file: Adrift.2018.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Adventureland.[2009.]Unrated Edition.DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Adventureland.[2009.]Unrated Edition.DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: African.Cats.2011.Bluray.english-sdh.srt
Processing file: After the Sunset 2004 BluRay 1080p AVC DTS-HD MA 5.1-HDH.srt
Processing file: After.2019.720p.BluRay.x264-DRONES-HI.srt
Processing file: After.Earth.2013.720p.BluRay.x264-SPARKS.srt
Processing file: Against.The.Ropes.2004.720p.WEBRip.x264.AAC-[YTS.MX].srt
Processing file: Agent.Cody.Banks.2.Destination.London.2004.BluRay.x265-RARBG.srt
Processing file: Agent.Cody.Banks.2003.iNTERNAL.DVDRip.x264-REGRET.srt
Text not found in sentences: Teacher: ...POINT 4968.          
Processing file: Akeelah.and.the.Bee.2006.720p.BluRay.H264.AAC-RARBG HI.srt
Skipping file: Akeelah.and.the.Bee.2006.720p.BluRay.H264.AAC-RARBG HI.srt as all values in the 'speaker' column are NA's.
Processing file: Aladdin.2019.1080p.WEBRip.x264-[YTS.srt
Processing file: Alex.and.Emma.2003.WEB-DL.x264-ION10.srt
Skipping file: Alex.and.Emma.2003.WEB-DL.x264-ION10.srt as all values in the 'speaker' column are NA's.
Processing file: Alex.Cross.2012.BRRIP.XVID.srt
Processing file: Alexander.2004.Ultimate.Cut.1080p.BluRay.x264.DTS-FGT.srt
Processing file: Alexander.and.the.Terrible.Horrible.No.Good.Very.Bad.Day.2014.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Alfie (2004) 1080p WEBRip.en sdh.srt
Processing file: Alice.in.Wonderland.2010.720p.BluRay.DTS.x264-CBGB.srt
Processing file: Aliens in the Attic DVDRip XviD-DiAMOND Eng.srt
Skipping file: Aliens in the Attic DVDRip XviD-DiAMOND Eng.srt as all values in the 'speaker' column are NA's.
Processing file: Aliens.Vs.Predator.Requiem.2007.1080p.BluRay.H264.AAC-RARBG-eng.srt
Skipping file: Aliens.Vs.Predator.Requiem.2007.1080p.BluRay.H264.AAC-RARBG-eng.srt as all values in the 'speaker' column are NA's.
Processing file: Alita.Battle.Angel.2019.1080p.HDRip.X264-EVO-HI.srt
Processing file: All.Eyez.on.Me.2017.720p.BluRay.H264.AAC-RARBG-HI.srt
Processing file: alli-longshots.en.HI.srt
Skipping file: alli-longshots.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: alli-maxpayne-xvid.en.HI.srt
Skipping file: alli-maxpayne-xvid.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: alli-paul-xvid.srt
Processing file: alli-proper-repo-xvid-cd1.srt
Processing file: alli-proper-repo-xvid-cd2.srt
Processing file: alliance-the.perfect.score-xvid.srt
Processing file: Almost.Christmas.2016.1080p.BluRay.x264-GECKOS.srt
Processing file: Aloha.2015.BluRay.1080p.eng_SDH.srt
Processing file: Alone In The Dark.English.srt
Skipping file: Alone In The Dark.English.srt as all values in the 'speaker' column are NA's.
Processing file: Along.Came.A.Spider.2001.720p.BrRip.x264.YIFY.CHI.srt
Skipping file: Along.Came.A.Spider.2001.720p.BrRip.x264.YIFY.CHI.srt as all values in the 'speaker' column are NA's.
Processing file: along_came_polly_x264_uSk.english.srt
Processing file: Alpha Dog MULTi BluRay 720p x264-HeMAN.srt
Processing file: Alpha.2018.1080p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: Amelia.DVDRip.XviD-NeDiVx.hi.srt
Processing file: American Outlaws (2001).srt
Skipping file: American Outlaws (2001).srt as all values in the 'speaker' column are NA's.
Processing file: American Pie 2.srt
Skipping file: American Pie 2.srt as all values in the 'speaker' column are NA's.
Processing file: American Pie 3 The Wedding[2003]DvDrip[Eng]-BugZ.srt
Skipping file: American Pie 3 The Wedding[2003]DvDrip[Eng]-BugZ.srt as all values in the 'speaker' column are NA's.
Processing file: american psycho_ the movie.srt
Skipping file: american psycho_ the movie.srt as all values in the 'speaker' column are NA's.
Processing file: American.Dreamz.2006.720p.BluRay.x264-BRMP.srt
Text not found in sentences: Stop, Mom.
 All right.
Processing file: American.Gangster.Unrated.2007.1080p.BluRay.x264.anoXmous_eng.srt
Text not found in sentences: NYPD, excuse me, Police Department.
 
Processing file: American.Reunion.2012.720p.UNRATED.BluRay.x264.DTS-HDChina.english.srt
Skipping file: American.Reunion.2012.720p.UNRATED.BluRay.x264.DTS-HDChina.english.srt as all values in the 'speaker' column are NA's.
Processing file: American.Ultra.2015.HDRip.XviD.AC3-EVO.Hi.srt
Processing file: An.American.Carol.2008.720p.BluRay.H264.AAC-RARBG.srt
Skipping file: An.American.Carol.2008.720p.BluRay.H264.AAC-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: An.American.Haunting.PROPER.DVDRip.XviD-DiAMOND.Hi.srt
Skipping file: An.American.Haunting.PROPER.DVDRip.XviD-DiAMOND.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Anacondas - The Hunt for the Blood Orchid .Screen Gems.2004.23.976 fps.English SDH.srt
Skipping file: Anacondas - The Hunt for the Blood Orchid .Screen Gems.2004.23.976 fps.English SDH.srt as all values in the 'speaker' column are NA's.
Processing file: Analyze.That.2002.1080p.Bluray.X264-DIMENSION.ENG_HI.srt
Processing file: Anchorman.2.The.Legend.Continues.2013.UNRATED.1080p.BluRay.x264-SPARKS.srt
Skipping file: Anchorman.2.The.Legend.Continues.2013.UNRATED.1080p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: Anchorman.Die.Legende.von.Ron.Burgundy.2004.German.AC3.DL.1080p.BluRay.x265-FuN.Hi.srt
Processing file: Angel.Eyes.2001.1080p.AMZN.WEB-DL.DDP5.1.H.264-pawel2006.srt
Processing file: Angel.Has.Fallen.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Angels.&.Demons.2009.1080p.BrRip.x264.YIFY+HI.srt
Skipping file: Angels.&.Demons.2009.1080p.BrRip.x264.YIFY+HI.srt as all values in the 'speaker' column are NA's.
Processing file: Anna.2019.1080p.WEB-DL.H264.AC3-EVO.Hi.srt
Processing file: Annabelle.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Annabelle.Comes.Home.2019.HC.HDRip.XviD.AC3-EVO-HI.srt
Skipping file: Annabelle.Comes.Home.2019.HC.HDRip.XviD.AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Annihilation.2018.720p.NF.WEBRip.DD5.1.x264-NTG.HI.srt
Skipping file: Annihilation.2018.720p.NF.WEBRip.DD5.1.x264-NTG.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Ant-Man.2015.WEBRip.x264-RARBG.HI.srt
Processing file: Ant.Man.and.the.Wasp.2018.720p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Any Given Sunday_enHI.srt
Processing file: Anything.Else.DVDRip.XViD-DVL.English.srt
Skipping file: Anything.Else.DVDRip.XViD-DVL.English.srt as all values in the 'speaker' column are NA's.
Processing file: Apocalypto.DVDRiP.XViD-DEiTY.CD1.English.HearingImpared.srt
Skipping file: Apocalypto.DVDRiP.XViD-DEiTY.CD1.English.HearingImpared.srt as all values in the 'speaker' column are NA's.
Processing file: Apocalypto.DVDRiP.XViD-DEiTY.CD2.English.HearingImpared.srt
Skipping file: Apocalypto.DVDRiP.XViD-DEiTY.CD2.English.HearingImpared.srt as all values in the 'speaker' column are NA's.
Processing file: Apollo.18.2011.720p.Bluray.x264-CBGB.Hi.srt
Processing file: Aquaman.2018.IMAX.720p.WEB-DL.H264.AC3-EVO.srt
Skipping file: Aquaman.2018.IMAX.720p.WEB-DL.H264.AC3-EVO.srt as all values in the 'speaker' column are NA's.
Processing file: Aquamarine.2006.720p.BluRay.H264.AAC-RARBG hi.srt
Processing file: Argo.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: Armored.[2009].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Armored.[2009].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Around The World in 80 Days_enHI.srt
Skipping file: Around The World in 80 Days_enHI.srt as all values in the 'speaker' column are NA's.
Processing file: Arrival.HDCAM.x264-TuttyFruity.en.srt
Skipping file: Arrival.HDCAM.x264-TuttyFruity.en.srt as all values in the 'speaker' column are NA's.
Processing file: arrow-faster.xvid.srt
Text not found in sentences: MAN 2 : Twenty-five dollar gift cert-- Brother, put down that bottle.
Processing file: arrow.lottery.ticket.en.HI.srt
Processing file: arw-measures.srt
Processing file: arw-moh.dvdrip.xvid.en.HI.srt
Processing file: arw-trait.dvdrip.xvid.srt
Skipping file: arw-trait.dvdrip.xvid.srt as all values in the 'speaker' column are NA's.
Processing file: As.Above.So.Below.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Assassination.Nation.2018.720p.BluRay.x264-DRONES-HI.srt
Skipping file: Assassination.Nation.2018.720p.BluRay.x264-DRONES-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Assassins Creed (2016).en.srt
Skipping file: Assassins Creed (2016).en.srt as all values in the 'speaker' column are NA's.
Processing file: Assault on Precinct 13.srt
Skipping file: Assault on Precinct 13.srt as all values in the 'speaker' column are NA's.
Processing file: Atlas Shrugged 2_The Strike-SPARKS.ENGLISH-HI.srt
Processing file: Austin.Powers.in.Goldmember.2002.720p.BluRay.x264-REVEiLLE.ENG_HI.srt
Processing file: Australia[2008]DvDRip-aXXo.en.HI.srt
Skipping file: Australia[2008]DvDRip-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Avatar.ECE.2009.1080p.BrRip.x264.bitloks.srt
Processing file: Avengers.Age.of.Ultron.2015.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Avengers.Endgame.2019.1080p.WEBRip.x264-[YTS.LT]-HI.srt
Processing file: Avengers.Infinity.War.2018.720p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: AVP.Alien.vs.Predator.2004.UNRATED.BluRay.x265-RARBG.srt
Skipping file: AVP.Alien.vs.Predator.2004.UNRATED.BluRay.x265-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: Baby Boy.srt
Skipping file: Baby Boy.srt as all values in the 'speaker' column are NA's.
Processing file: Baby Mama[Eng][Subs].srt
Processing file: bad eng cd1ripped by thor srt.srt
Processing file: bad eng cd2ripped by thor srt.srt
Processing file: Bad Teacher 2011 UNRATED 720p BluRay x264-Felony.Hi.srt
Processing file: Bad.Boys.II.2003.720p.BluRay.X264-AMIABLE-HI.srt
Processing file: Bad.Santa.2.2016.UNRATED.720p.BluRay.x264-DRONES-HI.srt
Skipping file: Bad.Santa.2.2016.UNRATED.720p.BluRay.x264-DRONES-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Bad.Times.at.the.El.Royale.2018.720p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Baggage.Claim.2013.DVDRip.x264-COCAIN-SDH.srt
Processing file: bald-thr5.srt
Skipping file: bald-thr5.srt as all values in the 'speaker' column are NA's.
Processing file: Bandits.2001.1080p.BluRay.H264.AAC-RARBG_Eng.srt
Skipping file: Bandits.2001.1080p.BluRay.H264.AAC-RARBG_Eng.srt as all values in the 'speaker' column are NA's.
Processing file: Bandslam.RERIP.DVDRip.XviD-DoNE.srt
Processing file: Barbershop.2002.720p.HDTV.DD5.1.x264-CtrlHD.srt
Skipping file: Barbershop.2002.720p.HDTV.DD5.1.x264-CtrlHD.srt as all values in the 'speaker' column are NA's.
Processing file: batman.begins-phrax.srt
Processing file: Battle.Los.Angeles.2011.R5.LiNE.Xvid {1337x}-Noir.srt
Skipping file: Battle.Los.Angeles.2011.R5.LiNE.Xvid {1337x}-Noir.srt as all values in the 'speaker' column are NA's.
Processing file: Battle.of.the.Year.2013.720p.BluRay.x264-GECKOS-sdh.srt
Processing file: Battlefield.Earth.2000.1080p.AMZN.WEB-DL.DDP5.1.H.264-monkee.eng.srt
Processing file: Battleship.2012.PROPER.720p.BluRay.x264-SPARKS.english.srt
Skipping file: Battleship.2012.PROPER.720p.BluRay.x264-SPARKS.english.srt as all values in the 'speaker' column are NA's.
Processing file: Baywatch.2017.UNRATED.720p.BluRay.x264-GECKOS.HI.srt
Processing file: BDRip.srt
Processing file: Beastly.PROPER.DVDRip.XviD-DEFACED.Hi.srt
Processing file: Beautiful.2000.WEBRip.srt
Text not found in sentences: Your Aunt Mona's up there.
 
Processing file: Beautiful.Creatures.2013.720p.BluRay.x264-SPARKS.srt
Skipping file: Beautiful.Creatures.2013.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: Beauty.and.the.Beast.2017.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Beauty.Shop.2005.1080p.BluRay.srt
Skipping file: Beauty.Shop.2005.1080p.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: Because Of Winn-Dixie 2005 DvDrip[Eng]-greenbud1969.srt
Processing file: Bedtime.Stories[2008].en.srt
Skipping file: Bedtime.Stories[2008].en.srt as all values in the 'speaker' column are NA's.
Processing file: Before.I.Fall.2017.720p.BluRay.x264-Replica.HI.srt
Processing file: Before.I.Go.To.Sleep.2014.LIMITED.720p.BluRay.X264-GECKOS.srt
Skipping file: Before.I.Go.To.Sleep.2014.LIMITED.720p.BluRay.X264-GECKOS.srt as all values in the 'speaker' column are NA's.
Processing file: BEHIND_ENEMY_LINES_ENG_25FPS.srt
Processing file: Beverly.Hills.Chihuahua[2008]DvDrip-aXXo.en.HI.srt
Skipping file: Beverly.Hills.Chihuahua[2008]DvDrip-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Bewitched.2005.WEBRip.AMZN.en.srt
Processing file: Beyond.the.Lights.2014.DC.720p.BluRay.x264-ALLiANCE-HI.srt
Processing file: Bicentennial Man.srt
Skipping file: Bicentennial Man.srt as all values in the 'speaker' column are NA's.
Processing file: Big Miracle (2012) DVDRip XviD SLiCK.srt
Processing file: Big MommasLike Father_Like Son[2011]BRRip XviD-ExtraTorrentRG.Hi.srt
Processing file: Big.Eyes.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Big.Mommas.House.2000.1080p.BluRay.REMUX.AVC.DTS-HD.MA.5.1-iROBOT.srt
Skipping file: Big.Mommas.House.2000.1080p.BluRay.REMUX.AVC.DTS-HD.MA.5.1-iROBOT.srt as all values in the 'speaker' column are NA's.
Processing file: Biker.Boyz.DVDRip.XviD-CFH.CD1.fixed.srt
Processing file: Biker.Boyz.DVDRip.XviD-CFH.CD2.fixed.srt
Processing file: Birth.2004.1080p.AMZN.WEB-DL.DD+5.1.srt
Skipping file: Birth.2004.1080p.AMZN.WEB-DL.DD+5.1.srt as all values in the 'speaker' column are NA's.
Processing file: Birthday.Girl.2001.1080p.WEBRip.DD5.1.x264-NTb.en.cc.srt
Skipping file: Birthday.Girl.2001.1080p.WEBRip.DD5.1.x264-NTb.en.cc.srt as all values in the 'speaker' column are NA's.
Processing file: Black and Blue.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Black Christmas 2006 Unrated BluRay 720p DTS x264-MgB [ETRG].srt
Skipping file: Black Christmas 2006 Unrated BluRay 720p DTS x264-MgB [ETRG].srt as all values in the 'speaker' column are NA's.
Processing file: Black.Christmas.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Black.Nativity.2013.720p.BluRay.srt
Processing file: Black.or.White.2014.720p.BluRay.H264.AAC-RARBG.srt
Processing file: Black.Panther.2018.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Blackhat 2015 1080p BRRip x264 DTS-JYK.srt
Processing file: BlacKkKlansman.2018.720p.WEB-DL.DD5.1.srt
Processing file: Blade II_English.srt
Skipping file: Blade II_English.srt as all values in the 'speaker' column are NA's.
Processing file: Blade.Trinity.2004.720p.BluRay.x264-SidBrothers_3.srt
Processing file: Blended.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Blinded.by.the.Light.2019.720p.BluRay.x264-AAA-HI.srt
Processing file: Blockers.2018.720p.BluRay.x264.DTS-HDC-HI.srt
Processing file: Blood.Work.2002.720p.BluRay.srt
Processing file: Blow.2001.720p.BRRip.srt
Processing file: Blu-ray.srt
Processing file: Blue.Crush.[2002].DVDRip.XviD-EN-HI.srt
Skipping file: Blue.Crush.[2002].DVDRip.XviD-EN-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Boat.Trip.2002.1080p.WEBRip.DD2.0.x264-NTb.srt
Skipping file: Boat.Trip.2002.1080p.WEBRip.DD2.0.x264-NTb.srt as all values in the 'speaker' column are NA's.
Processing file: Body.Of.Lies[2008]DvDrip-aXXo.en.HI.srt
Processing file: Boiler Room 2000 1080p BluRay DD5 1 x265-Chivaman.srt
Processing file: Bones.2001.1080p.BluRay.x264-HANDJOB.srt
Skipping file: Bones.2001.1080p.BluRay.x264-HANDJOB.srt as all values in the 'speaker' column are NA's.
Processing file: Boo.A.Madea.Halloween.2016.720p.BluRay.x264-GECKOS(1).srt
Skipping file: Boo.A.Madea.Halloween.2016.720p.BluRay.x264-GECKOS(1).srt as all values in the 'speaker' column are NA's.
Processing file: Boogeyman.2005.720p.BluRay.x264-BestHD-sdh.srt
Processing file: Book.Club.2018.720p.WEB-DL.X264.CAM.AUDIO.srt
Skipping file: Book.Club.2018.720p.WEB-DL.X264.CAM.AUDIO.srt as all values in the 'speaker' column are NA's.
Processing file: Book.of.Shadows.Blair.Witch.2.2000.DVDRip.XviD-UNKNOW.srt
Skipping file: Book.of.Shadows.Blair.Witch.2.2000.DVDRip.XviD-UNKNOW.srt as all values in the 'speaker' column are NA's.
Processing file: Booksmart.2019.1080p.NF.WEB-DL.DD5.1.srt
Skipping file: Booksmart.2019.1080p.NF.WEB-DL.DD5.1.srt as all values in the 'speaker' column are NA's.
Processing file: Borat.2006.720p.BrRip.x264.srt
Skipping file: Borat.2006.720p.BrRip.x264.srt as all values in the 'speaker' column are NA's.
Processing file: Born in China-HDC.ENGLISH-HI.srt
Processing file: Boys.and.Girls.English.by.GRuPoUToPiA.srt
Skipping file: Boys.and.Girls.English.by.GRuPoUToPiA.srt as all values in the 'speaker' column are NA's.
Processing file: Bratz.The.Movie.2007.WEBRip.Netflix.srt
Skipping file: Bratz.The.Movie.2007.WEBRip.Netflix.srt as all values in the 'speaker' column are NA's.
Processing file: Breach.2007.720p.BluRay.x264-.YTS.AM.srt
Processing file: Breaking.In.2018.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Breakthrough.2019.1080p.WEB-DL.H264.srt
Processing file: Brian.Banks.2018.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Brick Mansions 2014 DVDRip x264 AC3-MiLLENiUM.srt
Processing file: Bride Wars[Eng][Subs].srt
Processing file: Bridesmaids.720p.BluRay.x264-REFiNED.Hi.srt
Processing file: Bridget.Jones.Diary[2001]DvDrip[Eng]-FANTASTiC.srt
Processing file: Bridget.Jones.The.Edge.Of.Reason.2004.1080p.BluRay.x264-CiNEFiLE.ENG_HI.srt
Skipping file: Bridget.Jones.The.Edge.Of.Reason.2004.1080p.BluRay.x264-CiNEFiLE.ENG_HI.srt as all values in the 'speaker' column are NA's.
Processing file: Bridget.Joness.Baby.2016.1080p.BluRay.x264-SPARKS.English.srt
Processing file: Brightburn.2019.1080p.HC.HDRip.X264.srt
Processing file: Bring.It.On.2000.720p.BluRay.x264-PHOBOS-HI.srt
Processing file: Bringing_Down_the_House_(2003).En HI.srt
Processing file: Broken Lizards Club Dread (2004).srt
Skipping file: Broken Lizards Club Dread (2004).srt as all values in the 'speaker' column are NA's.
Processing file: Broken.City.2013.720p.BluRay.DTS.x264-PublicHD.srt
Skipping file: Broken.City.2013.720p.BluRay.DTS.x264-PublicHD.srt as all values in the 'speaker' column are NA's.
Processing file: Brooklyns.Finest.720p.Bluray.srt
Skipping file: Brooklyns.Finest.720p.Bluray.srt as all values in the 'speaker' column are NA's.
Processing file: Brown.Sugar.Eng.ToMane.srt
Skipping file: Brown.Sugar.Eng.ToMane.srt as all values in the 'speaker' column are NA's.
Processing file: Bruce Almighty.[2003].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Bruce Almighty.[2003].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Bruno.srt
Processing file: Bubble boy EN whole.srt
Processing file: Bucky.Larson.Born.To.Be.A.Star.2011.720p.BluRay.x264-ALLiANCE.eng.HI.srt
Processing file: Bullet.To.The.Head.2012.REPACK.720p.BluRay.x264-Felony.Hi.srt
Processing file: Bulletproof.Monk.2003.SLOSubs.720p.BRRip.x264-YIFY-eng.srt
Processing file: Bumblebee.2018.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Burn.After.Reading.2008.BluRay.1080p.DTS.x264.dxva-EuReKA.ENG_HI.srt
Processing file: Cabin Fever Unrated DC 720p fiveofseven zombiRG.srt
Skipping file: Cabin Fever Unrated DC 720p fiveofseven zombiRG.srt as all values in the 'speaker' column are NA's.
Processing file: capt c Mandolin EN.srt
Processing file: Captain America - The First Avenger (2011) BluRay.x264.srt
Processing file: Captain.America.The.Winter.Soldier.2014.1080p.BluRay.x264.YIFY-eng.srt
Processing file: Captain.Marvel.2019.HDRip.AC3.X264-CMRG-HI.srt
Processing file: Captain.Phillips.2013.720p.BluRay.X264-AMIABLE.srt
Processing file: Captive.2015.720p.BluRay.X264-AMIABLE-HI.srt
Processing file: Captive.State.2019.720p.BluRay.x264-MAYHEM-HI.srt
Skipping file: Captive.State.2019.720p.BluRay.x264-MAYHEM-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Carrie.2013.720p.BluRay.x264-SPARKS.srt
Processing file: Case.39.2009.BluRay.x265-RARBG.en.srt
Processing file: Cast Away (ENG) (Hearing).srt
Skipping file: Cast Away (ENG) (Hearing).srt as all values in the 'speaker' column are NA's.
Processing file: Cast Away CD1 (ENG) (Hearing).srt
Skipping file: Cast Away CD1 (ENG) (Hearing).srt as all values in the 'speaker' column are NA's.
Processing file: Cast Away CD2 (ENG) (Hearing).srt
Skipping file: Cast Away CD2 (ENG) (Hearing).srt as all values in the 'speaker' column are NA's.
Processing file: Catch That Kid.srt
Skipping file: Catch That Kid.srt as all values in the 'speaker' column are NA's.
Processing file: Catch.and.Release[2006].Dvdrip.Xvid.AC3[5.1]-RoCK.srt
Skipping file: Catch.and.Release[2006].Dvdrip.Xvid.AC3[5.1]-RoCK.srt as all values in the 'speaker' column are NA's.
Processing file: Catch.Me.If.You.Can.2002.DVDRip.XviD.Subs.EN-HI-UnSeeN.srt
Processing file: Cats And Dogs English (Hearing Impaired).srt
Processing file: Cats.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Cats.and.Dogs.The.Revenge.of.Kitty.Galore.DVDRip.XviD-ARROW.srt
Processing file: Catwoman.srt
Skipping file: Catwoman.srt as all values in the 'speaker' column are NA's.
Processing file: cbgb-greenzone720.eng.srt
Processing file: cbgb-olddogs720.srt
Skipping file: cbgb-olddogs720.srt as all values in the 'speaker' column are NA's.
Processing file: cbgb-sorcerersapprentice720.EN.srt
Processing file: Center.Stage.2000.720p.BluRay.X264-AMIABLE-HI.srt
Processing file: Cesar.Chaves.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Chappaquiddick.2017.1080p.BluRay.srt
Skipping file: Chappaquiddick.2017.1080p.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: Chappie.2015.1080p.WEB-DL.AAC2.0.H264-RARBG.srt
Skipping file: Chappie.2015.1080p.WEB-DL.AAC2.0.H264-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: Charlie St.Cloud 2010 BDRip-xvid.srt
Skipping file: Charlie St.Cloud 2010 BDRip-xvid.srt as all values in the 'speaker' column are NA's.
Processing file: Charlie.and.the.Chocolate.Factory.2005.BluRay.1080p.DTS.x264.dxva-wsp.ENG_HI.srt
Processing file: Charlie.Wilsons.War[2007]DvDrip-aXXo.eng.srt
Processing file: Charlies Angels.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Charlies.Angels.2000.REMASTERED.BluRay.x265-RARBG.en.srt
Processing file: Charlies.Angels.Full.Throttle.2003.BluRay.x265-RARBG.en.srt
Processing file: Chasing.Liberty.2004.1080p.WEB-DL.x264-aLD3N.srt
Processing file: Chasing.Mavericks.2012.720p.WEBRiP.XViD.AC3-LEGi0N_Subtitle - English.srt
Processing file: Cheaper by the Dozen [2003] DvDrip [Eng] BugZ.srt
Skipping file: Cheaper by the Dozen [2003] DvDrip [Eng] BugZ.srt as all values in the 'speaker' column are NA's.
Processing file: Cheaper.by.the.Dozen.2.2005.WEBRip.iTunes.srt
Processing file: Chernobyl Diaries 2012 Corrected English Sub.srt
Skipping file: Chernobyl Diaries 2012 Corrected English Sub.srt as all values in the 'speaker' column are NA's.
Processing file: Child.44.2015.720p.BluRay.srt
Processing file: Childs.Play.2019.720p.BluRay.x264-[YTS.LT].Hi.srt
Processing file: Christmas.with.the.Kranks.2004.WEBRip.Amazon.srt
Processing file: Christopher.Robin.2018.720p.BluRay.x264-.YTS.AM.srt
Processing file: Chronicle.2012.DVDRip.XviD-SPARKS.srt
Processing file: Cinderella Man - English SDH (29_970FPS).srt
Skipping file: Cinderella Man - English SDH (29_970FPS).srt as all values in the 'speaker' column are NA's.
Processing file: Cinderella.2015.HC.WEBRip.XviD.MP3-RARBG.srt
Processing file: Cirque.Du.Freak.The.Vampires.Assistant.2009.480p.BRRip.XviD.srt
Processing file: City.Of.Ember.2008.720p.BluRay.x264-SiNNERS.eng.srt
Skipping file: City.Of.Ember.2008.720p.BluRay.x264-SiNNERS.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Click.2006.WEBRip.Netflix.en[cc].srt
Processing file: Clockstoppers.2002.1080p.WEBRip.x264-RARBG.srt
Processing file: Closed.Circuit.2013.720p.BluRay.X264-AMIABLE-sdh.srt
Processing file: Cloud.Atlas.2012.RC.BDRip.STUDIO.AUDIO.XVID.AC3-5.1.HQ.Hive-CM8.HI.srt
Processing file: Cloverfield.2008.720p.BluRay.x264.srt
Skipping file: Cloverfield.2008.720p.BluRay.x264.srt as all values in the 'speaker' column are NA's.
Processing file: coatdq.dvdrip.xvid-deity.srt
Processing file: Cold Creek Manor (2003) CD1 -ALLiANCE.Eng-HI.srt
Processing file: Cold Creek Manor (2003) CD2 -ALLiANCE.Eng-HI.srt
Processing file: Cold.Mountain.2003.720p.Bluray.x264.anoXmous_eng.srt
Skipping file: Cold.Mountain.2003.720p.Bluray.x264.anoXmous_eng.srt as all values in the 'speaker' column are NA's.
Processing file: Cold.Pursuit.2019.1080p.WEB-DL.DD5.1.srt
Skipping file: Cold.Pursuit.2019.1080p.WEB-DL.DD5.1.srt as all values in the 'speaker' column are NA's.
Processing file: Collateral.2004.BluRay.1080p.DTS-HD.MA5.1.2Audio.x264-HDS.eng.srt
Skipping file: Collateral.2004.BluRay.1080p.DTS-HD.MA5.1.2Audio.x264-HDS.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Collateral.Beauty.2016.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Collateral.Damage[2002].srt
Processing file: College[2008]DvDrip-aXXo.en.HI.srt
Processing file: Conan.The.Barbarian.2011.BluRay.x265-RARBG.Hi.srt
Skipping file: Conan.The.Barbarian.2011.BluRay.x265-RARBG.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Confidence.PROPER.DVDRip.XViD-DEiTY.srt
Skipping file: Confidence.PROPER.DVDRip.XViD-DEiTY.srt as all values in the 'speaker' column are NA's.
Processing file: Connie.And.Carla.2004.DVDRip.XviD.iNT-TLF.eng.srt
Processing file: Constantine.2005.BluRay.720p.x264.DTS-WiKi-HI.srt
Processing file: Contagion.2011.Bluray.english-sdh.srt
Processing file: Contraband.2012.720p.BluRay.X264-AMIABLE.englsih.srt
Processing file: Cop Out (2010) 720p BluRay X264-AMIABLE.srt
Processing file: Corky Romano (2001).srt
Processing file: Countdown.2019.1080p.BluRay.x264-[YTS.srt
Skipping file: Countdown.2019.1080p.BluRay.x264-[YTS.srt as all values in the 'speaker' column are NA's.
Processing file: Couples Retreat.[2009].HD.DVDRIP.XVID.[Eng]-DUQA.srt.srt
Processing file: Courageous.2011.BluRay.720p.x264.srt
Skipping file: Courageous.2011.BluRay.720p.x264.srt as all values in the 'speaker' column are NA's.
Processing file: Cowboys.And.Aliens.2011.EXTENDED.720p.BluRay.x264-CROSSBOW.Hi.srt
Processing file: Crank-High Voltage[english subs]MZON3.srt
Processing file: Crank.srt
Skipping file: Crank.srt as all values in the 'speaker' column are NA's.
Processing file: Crawl.2019.HDRip.XviD.AC3-EVO-HI.srt
Skipping file: Crawl.2019.HDRip.XviD.AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Crazy.Beautiful.DVDRip.DivX-DOMiNiON.srt
Processing file: Crazy.Rich.Asians.2018.1080p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: Crazy.Stupid.Love.DVDRip.XviD-TWiZTED-CD1.srt
Processing file: Crazy.Stupid.Love.DVDRip.XviD-TWiZTED-CD2.srt
Processing file: Creature.2011.720p.BluRay.x264.AAC-[YTS.MX] sdh.srt
Processing file: Creed.2.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Crimson.Peak.2015.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Crocodile Dundee In Los Angeles.srt
Skipping file: Crocodile Dundee In Los Angeles.srt as all values in the 'speaker' column are NA's.
Processing file: Cursed.2005.UNRATED.1080p.BluRay.x264.DTS-FGT.srt
Skipping file: Cursed.2005.UNRATED.1080p.BluRay.x264.DTS-FGT.srt as all values in the 'speaker' column are NA's.
Processing file: Daddy.Day.Care.2003.WEB-DL.x264-RARBG.srt
Skipping file: Daddy.Day.Care.2003.WEB-DL.x264-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: Daddys.Home.2.2017.720p.BluRay.x264-BLOW.HI.srt
Processing file: Dance.Flick.2009 UNRATED.BDRip.XviD-NeDiVx.NoRar English subtitle(Dj Roobs release).srt
Skipping file: Dance.Flick.2009 UNRATED.BDRip.XviD-NeDiVx.NoRar English subtitle(Dj Roobs release).srt as all values in the 'speaker' column are NA's.
Processing file: Dante.srt
Skipping file: Dante.srt as all values in the 'speaker' column are NA's.
Processing file: DareDevil.Directors.Cut.DVDRip.XviD-DoNE.CD1.srt
Skipping file: DareDevil.Directors.Cut.DVDRip.XviD-DoNE.CD1.srt as all values in the 'speaker' column are NA's.
Processing file: DareDevil.Directors.Cut.DVDRip.XviD-DoNE.CD2.srt
Skipping file: DareDevil.Directors.Cut.DVDRip.XviD-DoNE.CD2.srt as all values in the 'speaker' column are NA's.
Processing file: Dark Blue 2002 1080p Blu-ray AVC DTS-HD MA 5.srt
Processing file: Dark.Phoenix.2019.720p.BluRay.srt
Processing file: Dark.Shadows.2012.1080p.BluRay.x264.YIFY.srt
Processing file: Dark.Skies.2013.720p.BluRay.DTS.x264-HDWinG.srt
Skipping file: Dark.Skies.2013.720p.BluRay.DTS.x264-HDWinG.srt as all values in the 'speaker' column are NA's.
Processing file: Dark.Water.2005.720p.BluRay.DTS.x264-XSHD-hi.srt
Skipping file: Dark.Water.2005.720p.BluRay.DTS.x264-XSHD-hi.srt as all values in the 'speaker' column are NA's.
Processing file: dash-yesman.en.HI.srt
Processing file: DATE MOVIE UNRATED[2006]DvdRip.avi[weezil420].srt
Skipping file: DATE MOVIE UNRATED[2006]DvdRip.avi[weezil420].srt as all values in the 'speaker' column are NA's.
Processing file: Dawn.Of.The.Dead.2004.1080p.HDDVD.x264-hV.ENG_HI.srt
Processing file: Dawn.of.the.Planet.of.the.Apes.2014.1080p.BluRay.x264-SPARKS.srt
Skipping file: Dawn.of.the.Planet.of.the.Apes.2014.1080p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: Daybreakers.[2009].R5.DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Daybreakers.[2009].R5.DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Dead.Man.Down.2013.720p.BluRay.x264.DTS-HDWinG.srt
Processing file: Dead.Silence.2007.1080p.BluRay.x264.YIFY.srt
Processing file: Deadpool.2.2018.Super.Duper.Cut.UNRATED.720p.AMZN.WEBRip.DDP5.1.x264-NTG-HI.srt
Processing file: Dear John.[2010].DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Processing file: Death at a Funeral.[2010].DVDRIP.H264.[Eng]-DUQA.srt
Skipping file: Death at a Funeral.[2010].DVDRIP.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Death of a Nation (2018).srt
Processing file: Death.Race.(2008)..[English.subtitles].by.SDGInn.srt
Processing file: Death.Sentence[2007][Unrated.Edition]DvDrip[Eng]-aXXo.en.srt
Skipping file: Death.Sentence[2007][Unrated.Edition]DvDrip[Eng]-aXXo.en.srt as all values in the 'speaker' column are NA's.
Processing file: Death.to.Smoochy.2002.REPACK.1080p.AMZN.WEB-DL.DD5.1.x264-ABM.en.sdh.srt
Skipping file: Death.to.Smoochy.2002.REPACK.1080p.AMZN.WEB-DL.DD5.1.x264-ABM.en.sdh.srt as all values in the 'speaker' column are NA's.
Processing file: Deception[2008]DvDrip-aXXo.en.HI.srt
Skipping file: Deception[2008]DvDrip-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Deck.the.Halls.2006.BluRay.x265-RARBG.srt
Processing file: Deja Vu (2006).srt
Processing file: Deliver.us.From.Evil.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Delivery.Man2013.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Derailed[2005]Unrated.DvDrip[Eng]-aXXo.srt
Skipping file: Derailed[2005]Unrated.DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Deuce Bigalow_improved.srt
Skipping file: Deuce Bigalow_improved.srt as all values in the 'speaker' column are NA's.
Processing file: Devil.2010.DVDRip.XviD-AMIABLE.Hi.srt
Processing file: Devils.Due.2014.HDRip.x264.AC3-FooKaS.Hi.srt
Processing file: devise-12roundsdvd.en.HI.srt
Processing file: devise-tutbr.en.HI.srt
Processing file: dfn-bloodd1080p.English.srt
Skipping file: dfn-bloodd1080p.English.srt as all values in the 'speaker' column are NA's.
Processing file: Diary.Of.A.Wimpy.Kid.Dog.Day.2012.DVDRip.XviD-iLG.eng.srt
Processing file: Diary.Of.A.Wimpy.Kid.DVDRip.XviD-ARROW.srt
Processing file: Diary.of.a.Wimpy.Kid.Rodrick.Rules.2011.BRRip XviD-SaM.Hi.srt
Processing file: Diary.of.a.Wimpy.Kid.The.Long.Haul.2017.720p.BluRay.x264-DRONES-HI.srt
Processing file: Dickie.Roberts.Former.Child.Star.2003.WEBRip.x265-RARBG_HI.en.srt
Processing file: Did.You.Hear.About.the.Morgans.2009.WEBRip.Amazon.srt
Skipping file: Did.You.Hear.About.the.Morgans.2009.WEBRip.Amazon.srt as all values in the 'speaker' column are NA's.
Processing file: Dinner.for.Schmucks.720p.Bluray.x264-CBGB.Hi.srt
Skipping file: Dinner.for.Schmucks.720p.Bluray.x264-CBGB.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Dirty Dancing Havana Nights.srt
Skipping file: Dirty Dancing Havana Nights.srt as all values in the 'speaker' column are NA's.
Processing file: Disaster.Movie.2008.WEB-DL.LIONSGATE.en.srt
Processing file: Disneynature.Bears.2014.WEB-DL.DSNP.srt
Processing file: Disneynature.Chimpanzee.2012.WEB-DL.DSNP.srt
Processing file: District 9.[2009].PREMIERE.DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: District 9.[2009].PREMIERE.DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: disturbia.srt
Skipping file: disturbia.srt as all values in the 'speaker' column are NA's.
Processing file: Divergent.2014.720p.BluRay.x264-SPARKS.srt
Processing file: django.unchained.2012.720p.bluray.srt
Skipping file: django.unchained.2012.720p.bluray.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-annapolis.en.HI.srt
Skipping file: dmd-annapolis.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-awake.srt
Skipping file: dmd-awake.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-brigett.eng.srt
Skipping file: dmd-brigett.eng.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-catchafire.eng.srt
Text not found in sentences: Earlier this week, Minister of Police,
Mr. Louis le Grange, warned that South Africa is in a virtual state of war...
 
Processing file: dmd-charliebartlett.en.HI.srt
Processing file: dmd-coas.en.HI.srt
Skipping file: dmd-coas.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-collegeroadtrip.en.HI.srt
Processing file: dmd-constgard-cd1-www.legendaz.com.br.srt
Skipping file: dmd-constgard-cd1-www.legendaz.com.br.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-constgard-cd2-www.legendaz.com.br.srt
Processing file: dmd-cott.en.srt
Processing file: dmd-danirl.srt
Skipping file: dmd-danirl.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-gonebg.srt
Processing file: dmd-gtd [HI].srt
Processing file: dmd-herbiefl.srt
Skipping file: dmd-herbiefl.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-hjntiya.en.HI.srt
Processing file: dmd-hjntiyb.en.HI.srt
Processing file: dmd-idlewild-cd1.en.HI.srt
Processing file: dmd-idlewild-cd2.en.HI.srt
Text not found in sentences: She killing you, Boss.
 
Processing file: dmd-landofdead.srt
Skipping file: dmd-landofdead.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-mollyh.en.HI.srt
Skipping file: dmd-mollyh.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-p2.en.HI.srt
Processing file: dmd-perfectman.HI.ENG.srt
Skipping file: dmd-perfectman.HI.ENG.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-sfchunli.en.HI.srt
Skipping file: dmd-sfchunli.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-smartpeople.en.HI.srt
Processing file: dmd-spiderwick.en.HI.srt
Processing file: dmd-sydney.HI.srt
Skipping file: dmd-sydney.HI.srt as all values in the 'speaker' column are NA's.
Processing file: dmd-twm1.srt
Processing file: dmd-twm2.srt
Processing file: dmd-whrj.en.HI.srt
Processing file: dmd-wih.srt
Skipping file: dmd-wih.srt as all values in the 'speaker' column are NA's.
Processing file: dmt-honey.srt
Skipping file: dmt-honey.srt as all values in the 'speaker' column are NA's.
Processing file: dmt-je_hearing_impaired.srt
Skipping file: dmt-je_hearing_impaired.srt as all values in the 'speaker' column are NA's.
Processing file: dmt-rof.srt
Skipping file: dmt-rof.srt as all values in the 'speaker' column are NA's.
Processing file: dmt-seeker.english.srt
Processing file: Do.You.Believe.2015.720p.BluRay.X264-AMIABLE.hi.srt
Skipping file: Do.You.Believe.2015.720p.BluRay.X264-AMIABLE.hi.srt as all values in the 'speaker' column are NA's.
Processing file: DOA.Dead.or.Alive.2006.1080p.BrRip.x264.YIFY.srt
Processing file: Doctor.Sleep.2019.DC.720p.BluRay.srt
Skipping file: Doctor.Sleep.2019.DC.720p.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: Doctor.Strange.2016.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Dodgeball.2004.1080p.BluRay.H264.srt
Skipping file: Dodgeball.2004.1080p.BluRay.H264.srt as all values in the 'speaker' column are NA's.
Processing file: Dog.Days.2018.1080p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Dolphin.Tale.2.2014.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Dolphin.Tale.720p.BluRay.x264-REFiNED.Hi.srt
Processing file: Domino[2005]DvDrip[Eng]-aXXo.srt
Processing file: Don.Jon.2013.1080p.BluRay.x264-SPARKS-SDH.srt
Processing file: Dont.Be.Afraid.Of.The.Dark.2010.HDRip.XviD-ViP3R.Hi.srt
Processing file: Dont.Breathe.2016.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Dont.Let.Go.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Dont.Say.A.Word.2001.ALL.BluRay.en.srt
Processing file: Doomsday.2008.Unrated.srt
Processing file: Doom[2005]DVDrip[ENG]-MissRipZ.srt
Skipping file: Doom[2005]DVDrip[ENG]-MissRipZ.srt as all values in the 'speaker' column are NA's.
Processing file: Dope 2015 1080p BluRay x264 DTS-JYK-eng.srt
Processing file: Dora.and.the.Lost.City.of.Gold.2019.1080p.BluRay.x264-DRONES.srt
Skipping file: Dora.and.the.Lost.City.of.Gold.2019.1080p.BluRay.x264-DRONES.srt as all values in the 'speaker' column are NA's.
Processing file: Downton.Abbey.2019.1080p.WEB-DL.DD5.1.srt
Processing file: dp-bad.santa.2003.unrated.ws.int.dvdrip.xvid.srt
Processing file: dr.dolittle.2.2001.720p.hdtv.x264-regret.srt
Skipping file: dr.dolittle.2.2001.720p.hdtv.x264-regret.srt as all values in the 'speaker' column are NA's.
Processing file: Dracula.Untold.2014.720p.BluRay.x264-VeDeTT.srt
Processing file: Draft.Day.2014.720p.BluRay.X264-AMIABLE-HI.srt
Processing file: drag.me.to.hell.dvdrip.xvid-imbt.EN+.srt
Processing file: Dragonball.Evolution.DVDRip.XviD-DoNE.(Hi).srt
Skipping file: Dragonball.Evolution.DVDRip.XviD-DoNE.(Hi).srt as all values in the 'speaker' column are NA's.
Processing file: Dragonfly[2002]DvDrip[Eng]-aXXo.srt
Skipping file: Dragonfly[2002]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Dream House 2011 BluRay Bdrip x264 1080p 720p.srt
Processing file: Dreamcatcher-[2003][DvDrip]-Demonuk[NIKONRG].srt
Processing file: Dreamer.Inspired.By.A.True.Story.2005.720p.BluRay.DTS.x264-UxO.srt
Processing file: Dredd 3D.[2012].DVDRIP.DIVX.srt
Skipping file: Dredd 3D.[2012].DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Drive Angry.srt
Processing file: Drive.srt
Processing file: Drumline2002-English.srt
Processing file: Dude.Wheres.My.Car.2000.720p.BD5.x264-IGUANA.srt
Skipping file: Dude.Wheres.My.Car.2000.720p.BD5.x264-IGUANA.srt as all values in the 'speaker' column are NA's.
Processing file: Due Date (2010).Arrow.En.srt
Processing file: Duece Bigalow European gigolo KAXXON.srt
Skipping file: Duece Bigalow European gigolo KAXXON.srt as all values in the 'speaker' column are NA's.
Processing file: Duets.2000.720p.BluRay.x264.srt
Skipping file: Duets.2000.720p.BluRay.x264.srt as all values in the 'speaker' column are NA's.
Processing file: Dumb.And.Dumber.To.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Dumb.and.Dumberer.When.Harry.Met.Lloyd.2003.1080p.WEBRip.x264-RARBG.srt
Processing file: Dumbo.2019.720p.Bluray.srt
Processing file: Duplex (2003) DVDrip DivX {CyberGhost}.srt
Processing file: Duplicity.2009.PROPER.DVDRip.XviD-Replicas.(Hi).srt
Processing file: DVDRip.srt
Processing file: DvDrip[Eng]-FXG [and BRRip.XviD.srt
Processing file: Dylan.Dog.Dead.of.Night.2011.720p.1080p.HI.srt
Processing file: Eagle.Eye.2008.720p.BluRay.DTS.x264-ESiR.srt
Processing file: Earth.to.Echo.2014.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Easy A (2010) [720p] [BluRay] [YTS.MX]_HI.srt
Skipping file: Easy A (2010) [720p] [BluRay] [YTS.MX]_HI.srt as all values in the 'speaker' column are NA's.
Processing file: Eat.Pray.Love.2010.WEB-DL.NF.en.srt
Processing file: Edge of Darkness.[2010].R5.DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Skipping file: Edge of Darkness.[2010].R5.DVDRIP.INTEL.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Edge.of.Tomorrow.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Eight.Below[2006]DvDrip[Eng]-aXXo.srt
Skipping file: Eight.Below[2006]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: El.Chicano.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: Elektra[2005]DvDrip[Eng][HI]-aXXo.srt
Skipping file: Elektra[2005]DvDrip[Eng][HI]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Elf.2003.1080p.BluRay.x264.anoXmous_eng.srt
Processing file: Elizabethtown.2005.720p.BluRay.x264.AAC-[YTS.srt
Skipping file: Elizabethtown.2005.720p.BluRay.x264.AAC-[YTS.srt as all values in the 'speaker' column are NA's.
Processing file: Ella.Enchanted.2004.BluRay.x264-CiNEFiLE.en.srt
Skipping file: Ella.Enchanted.2004.BluRay.x264-CiNEFiLE.en.srt as all values in the 'speaker' column are NA's.
Processing file: Elysium.2013.2160p.UHD.BluRay.x265.HDR.DD+5.1-Pahe.in.srt
Processing file: Employee.Of.The.Month.2006.WEBRip.Amazon.srt
Processing file: EN.Invictus[2009]DvDrip[Eng]-FXG.srt
Processing file: End.of.The.Spear.AMZN.1080p.WEB-DL.DDP5.1.H.264-BLUTONiUM_[eng].srt
Processing file: End.Of.Watch.2012.RETAIL.720p.BluRay.DTS.x264-PublicHD.eng.srt
Skipping file: End.Of.Watch.2012.RETAIL.720p.BluRay.DTS.x264-PublicHD.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Enders.Game.2013.720p.BluRay.x264-SPARKS-SDH.srt
Processing file: Endless.Love.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Enemy at the Gates (BDrip 1080p) x264 bluray (2001).engHI.srt
Skipping file: Enemy at the Gates (BDrip 1080p) x264 bluray (2001).engHI.srt as all values in the 'speaker' column are NA's.
Processing file: ENG HI (color).srt
Skipping file: ENG HI (color).srt as all values in the 'speaker' column are NA's.
Processing file: english SDH.srt
Processing file: English.srt
Skipping file: English.srt as all values in the 'speaker' column are NA's.
Processing file: ENG_SRT.srt
Skipping file: ENG_SRT.srt as all values in the 'speaker' column are NA's.
Processing file: Enough.WEBRip.Netflix.en[cc].srt
Skipping file: Enough.WEBRip.Netflix.en[cc].srt as all values in the 'speaker' column are NA's.
Processing file: Entourage.2015.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Envy.DVDRiP.XviD-DEiTY.srt
Skipping file: Envy.DVDRiP.XviD-DEiTY.srt as all values in the 'speaker' column are NA's.
Processing file: Epic.Movie.Unrated.DVDRiP-DEiTY.hearingimp.srt
Skipping file: Epic.Movie.Unrated.DVDRiP-DEiTY.hearingimp.srt as all values in the 'speaker' column are NA's.
Processing file: Eragon 1080p by Bokutox.srt
Skipping file: Eragon 1080p by Bokutox.srt as all values in the 'speaker' column are NA's.
Processing file: Erin.Brockovich.2000.1080p.BluRay.x265-RARBG_eng_HI.srt
Skipping file: Erin.Brockovich.2000.1080p.BluRay.x265-RARBG_eng_HI.srt as all values in the 'speaker' column are NA's.
Processing file: Escape.Plan.2013.720p.BluRay.x264-SPARKS.srt
Processing file: Escape.Room.2019.720p.WEBRip.x264-[YTS.srt
Processing file: Eternal.Sunshine.Of.The.Spotless.Mind.2004.HDRip.XViD.AC3-PRoDJi.srt
Skipping file: Eternal.Sunshine.Of.The.Spotless.Mind.2004.HDRip.XViD.AC3-PRoDJi.srt as all values in the 'speaker' column are NA's.
Processing file: Eurotrip (Unrated) - English Hearing Impaired (29_970FPS).srt
Skipping file: Eurotrip (Unrated) - English Hearing Impaired (29_970FPS).srt as all values in the 'speaker' column are NA's.
Processing file: Evan.Almighty[2007]DvDrip[Eng]-aXXo.srt
Processing file: Everest.2015.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Everything.Everything.2017.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Evil.Dead.2013.720p.BluRay.x264.DTS-HDWinG.srt
Processing file: ewdp-school.xvid.srt
Skipping file: ewdp-school.xvid.srt as all values in the 'speaker' column are NA's.
Processing file: Exit Wounds (engelsk hear imp).srt
Processing file: Exodus.Gods.and.Kings.2014.720p.BluRay.X264-AMIABLE.srt
Processing file: Exorcist.The.Beginning.2004.1080p.BluRay.x264.YIFY-eng.srt
Skipping file: Exorcist.The.Beginning.2004.1080p.BluRay.x264.YIFY-eng.srt as all values in the 'speaker' column are NA's.
Processing file: Extract.BDRip.XviD-DiAMOND.srt
Processing file: f-war.horse.720.english.srt
Processing file: Fahrenheit.11-9.2018.720p.AMZN.WEB-DL.DDP5.1.H.264-NTG.EN HOH.srt
Skipping file: Fahrenheit.11-9.2018.720p.AMZN.WEB-DL.DDP5.1.H.264-NTG.EN HOH.srt as all values in the 'speaker' column are NA's.
Processing file: Failure.to.Launch.2006.WEBRip.Amazon.srt
Processing file: Fantastic Four [2005].srt
Skipping file: Fantastic Four [2005].srt as all values in the 'speaker' column are NA's.
Processing file: Fantastic.Beasts.and.Where.to.Find.Them.2016.1080p.BluRay.x264.DTS-FGT.srt
Processing file: Fantastic.Beasts.The.Crimes.of.Grindelwald.2018.V2.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Fantastic.Four.2015.720p.BluRay.x264-GECKOS.HI.srt
Processing file: Fantastic.Four.Rise.of.the.Silver.Surfer.2007.WEB-DL.DSNP.srt
Processing file: Fast.Five.2011.720.BrRip.x264.YIFY.srt
Processing file: Fast.Furious.Presents.Hobbs.Shaw.2019.720p.WEBRip.x264-YTS.LT-HI.srt
Processing file: Father.Figures.2017.720p.BluRay.x264-GECKOS.HI.srt
Processing file: Fever.Pitch.2005.720p.BluRay.x264-PSYCHD.HI.srt
Skipping file: Fever.Pitch.2005.720p.BluRay.x264-PSYCHD.HI.srt as all values in the 'speaker' column are NA's.
Processing file: fico-arthurtc-cd1.en.HI.srt
Skipping file: fico-arthurtc-cd1.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: fico-arthurtc-cd2.en.HI.srt
Skipping file: fico-arthurtc-cd2.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Fifty.Shades.Darker.2017.UNRATED.720p.BluRay.x264-DRONES.HI.srt
Processing file: Fifty.Shades.Freed.2018.UNRATED.720p.BluRay.x264-DRONES-HI.srt
Processing file: Fifty.Shades.of.Grey.2015.UNRATED.720p.BluRay.X264-AMIABLE.srt
Processing file: Final Destination 1 2000.eng hi.srt
Processing file: Final Destination 2 2003.eng hi.srt
Processing file: Final.Destination.3.2006.1080p.Bluray.x264.anoXmous_eng.srt
Processing file: Final.Destination.5.2011.720p.Bluray.srt
Processing file: Fireproof (2008).DVDRip.HI.cc.en.AFFRM.srt
Processing file: Firewall - English SDH (25FPS).srt
Processing file: First Daughter.srt
Skipping file: First Daughter.srt as all values in the 'speaker' column are NA's.
Processing file: First.Man.2018.HC.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Fist.Fight.2017.720p.BluRay.x264-DRONES-HI.srt
Processing file: Five.Feet.Apart.2019.720p.HQ.HDCAM.900MB.1xbet.x264-BONSAI-HI.srt
Processing file: flame-push.2009.open.matte.1080p.bluray.x264.srt
Skipping file: flame-push.2009.open.matte.1080p.bluray.x264.srt as all values in the 'speaker' column are NA's.
Processing file: Flash.Of.Genius[2008]DvDrip-aXXo.en.HI.srt
Processing file: Flight.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: Flight.Of.The.Phoenix[2004]DvDrip[Eng]-aXXo.srt
Skipping file: Flight.Of.The.Phoenix[2004]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Flightplan[2005]DvDrip[Eng]-aXXo.srt
Skipping file: Flightplan[2005]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Flyboys (2006).DVDRip.HI.cc.en.20FOX.srt
Processing file: Focus.2015.720p.BluRay.x264-SPARKS.srt
Processing file: Fools.Gold[2008]DvDrip-aXXo.en.HI.srt
Processing file: Footloose.2011.DVDRIP.X264.AAC.CrEwSaDe.Hi.srt
Processing file: For Colored Girls.[2010].DVDRIP.DIVX.[Eng]-DUQA.srt
Skipping file: For Colored Girls.[2010].DVDRIP.DIVX.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Ford.V.Ferrari.2019.720p.WEBRip.x264.AAC-[YTS.srt
Processing file: Forever My Girl 720p.WEB-DL.850MB.MkvCage-HI.srt
Skipping file: Forever My Girl 720p.WEB-DL.850MB.MkvCage-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Forgetting.Sarah.Marshall.2008.720p.BluRay.x264-SiNNERS.engHI.srt
Processing file: Forráskód (Source Code) (2011) (BRRip).srt
Processing file: Four Christmases.srt
Processing file: Four.Brothers.2005.BluRay.x265-RARBG.en.srt
Skipping file: Four.Brothers.2005.BluRay.x265-RARBG.en.srt as all values in the 'speaker' column are NA's.
Processing file: Fracture.2007.10800p.BrRip.x264.YIFY.srt
Processing file: Frailty.2001.BluRay.x264-CiNEFiLE.en.srt
Processing file: Freaky.Friday.(English).XViD-DEiTY.srt
Skipping file: Freaky.Friday.(English).XViD-DEiTY.srt as all values in the 'speaker' column are NA's.
Processing file: Fred.Claus.2007.1080p.BluRay.x264.DD5.srt
Processing file: Freddy vs Jason 2003 DvDrip[Eng]-greenbud1969.Hi.srt
Skipping file: Freddy vs Jason 2003 DvDrip[Eng]-greenbud1969.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Frequency (2000) 1080p BluRay.en SDH.srt
Processing file: Friday Night Lights[2004]DvDrip[Eng]-Grimmo.srt
Skipping file: Friday Night Lights[2004]DvDrip[Eng]-Grimmo.srt as all values in the 'speaker' column are NA's.
Processing file: Friday.After.Next.2002.1080p.WEBRip.x264-[YTS.AM] sdh.srt
Processing file: Friday.the.13th.2009.THEATRICAL.720p.BluRay.x264-SADPANDA-HI.srt
Processing file: Friends.with.Benefits.2011.ALL Bluray version.Hi.srt
Processing file: Fright.Night.2011.720p.1080p.BluRay.HI.srt
Processing file: From Hell_ENG.sub.srt
Processing file: From Justin To Kelly.srt
Processing file: Fun Size (2012) BluRay Bdrip Brrip x264 1080p 720p 480p.srt
Processing file: Fun with Dick and Jane.[2005].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Fun with Dick and Jane.[2005].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Funny People (2009) DVDRip XviD-MAXSPEED.en.HI.srt
Processing file: Furious.6.2013.720p.WEB-DL.XviD.AC3-ELiTE.srt
Processing file: Furious.Seven.2015.EXTENDED.720p.BluRay.x264-SPARKS.srt
Processing file: Furry.Vengeance.(2010).DVD.Rip-Felony.srt
Processing file: Fury.2014.1080p.WEB-DL.DD5.1.srt
Skipping file: Fury.2014.1080p.WEB-DL.DD5.1.srt as all values in the 'speaker' column are NA's.
Processing file: G.I.Joe.Retaliation.2013.Extended.Action.Cut.720p.BluRay.x264-VeDeTT.srt
Skipping file: G.I.Joe.Retaliation.2013.Extended.Action.Cut.720p.BluRay.x264-VeDeTT.srt as all values in the 'speaker' column are NA's.
Processing file: GalaxyQuest.srt
Skipping file: GalaxyQuest.srt as all values in the 'speaker' column are NA's.
Processing file: Game.Night.2018.1080p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Gamer.2009.480p.BRRip.XviD.AC3-ViSiON.srt
Skipping file: Gamer.2009.480p.BRRip.XviD.AC3-ViSiON.srt as all values in the 'speaker' column are NA's.
Processing file: Gangs of New York (2002) 1080p H.srt
Processing file: Gangster.Squad.2013.720p.BluRay.x264-SPARKS.eng.srt
Skipping file: Gangster.Squad.2013.720p.BluRay.x264-SPARKS.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Gemini Man 2019 1080p WEB-DL H264 AC3-EVO-HI.srt
Skipping file: Gemini Man 2019 1080p WEB-DL H264 AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Get Him to the Greek (2010) DVDRip XviD-MAXSPEED www.torentz.3xforum.ro.en.srt
Text not found in sentences: Except for African Child.
 
Text not found in sentences: I love African Child.
 
Text not found in sentences: Who knows the lyrics to African Child?
 
Processing file: Get.Carter.2000.720p.BluRay.x264-HD4U-HI.srt
Processing file: Get.Hard.2015.UNRATED.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Get.On.Up.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Get.Over.It .2001.DVDrip.Xvid.dCd.English.srt
Skipping file: Get.Over.It .2001.DVDrip.Xvid.dCd.English.srt as all values in the 'speaker' column are NA's.
Processing file: Get.Smart[2008]DvDrip-aXXo.en.HI.srt
Processing file: Getaway.2013.720p.BluRay.x264.YIFY-eng.srt
Skipping file: Getaway.2013.720p.BluRay.x264.YIFY-eng.srt as all values in the 'speaker' column are NA's.
Processing file: Ghost Rider.SDHH.srt
Processing file: Ghost Ship 2002 en.srt
Processing file: Ghost.Rider.Spirit.Of.Vengeance.2011.720p.BluRay.X264-SPARKS.english.srt
Processing file: Ghostbusters.2016.EXTENDED.720p.BluRay.x264-DRONES.HI.srt
Processing file: Ghosts.of.Girlfriends.Past.DVDRip.XviD-DASH.srt
Processing file: Ghosts.of.Mars.2001.720p.BluRay.x264-BestHD-sdh.srt
Processing file: Gigli.ENG.25fps.[arlanda].srt
Skipping file: Gigli.ENG.25fps.[arlanda].srt as all values in the 'speaker' column are NA's.
Processing file: Gladiator.Exttended.Cut.2000.BRRip.XvidHD.720p-NPW.srt
Skipping file: Gladiator.Exttended.Cut.2000.BRRip.XvidHD.720p-NPW.srt as all values in the 'speaker' column are NA's.
Processing file: Glass.2019.NEW.HDCAM.x264.srt
Processing file: Glee.The.3D.Concert.Movie.2011.BDRip.XviD-Counterfeit.Hi.srt
Processing file: Glitter 2001 1080p WEB-DL x264 DD5.1.srt
Skipping file: Glitter 2001 1080p WEB-DL x264 DD5.1.srt as all values in the 'speaker' column are NA's.
Processing file: Gods Not Dead 2014 720p BRRip x264 AC3-EVO.srt
Skipping file: Gods Not Dead 2014 720p BRRip x264 AC3-EVO.srt as all values in the 'speaker' column are NA's.
Processing file: Gods.and.Generals.2003.Extended.Cut.BluRay.720p.DTS.x264-CHD.srt
Processing file: Godzilla.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Godzilla.King.of.the.Monsters.2019.HC.HDRip.XviD.AC3-EVO-HI.srt
Skipping file: Godzilla.King.of.the.Monsters.2019.HC.HDRip.XviD.AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Going.in.Style.2017.720p.BluRay.x264-DRONES.HI.srt
Processing file: Gold.2016.720p.BluRay.x264-[YTS.AG].en.srt
Processing file: Gone.Girl.2014.1080p.BluRay.x264-SPARKS.srt
Processing file: Gone.in.60.Seconds.2000.WEB-DL.DSNP.srt
Skipping file: Gone.in.60.Seconds.2000.WEB-DL.DSNP.srt as all values in the 'speaker' column are NA's.
Processing file: Good Boy (2003) English for hearing-impaired.srt
Processing file: Good.Boys.2019.720p.BluRay.x264-DRONES-HI.srt
Skipping file: Good.Boys.2019.720p.BluRay.x264-DRONES-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Goosebumps.2.Haunted.Halloween.2018.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Gotti.2018.720p.BluRay.x264-GUACAMOLE-HI.srt
Processing file: Grandmas Boy.2006.UNRATED.DVDRip.XviD-DiAMOND.srt
Skipping file: Grandmas Boy.2006.UNRATED.DVDRip.XviD-DiAMOND.srt as all values in the 'speaker' column are NA's.
Processing file: Gravity.2013.BluRay.720p.x264.DTS-HDWinG.srt
Processing file: Green Lantern[2011]DVDRip XviD-ExtraTorrentRG.srt
Processing file: Gridiron.Gang.2006.BluRay.x265-RARBG.en.srt
Processing file: Grind.srt
Processing file: Grown Ups 2.[2013].DVDRIP.DIVX.srt
Skipping file: Grown Ups 2.[2013].DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Grown Ups 2010 DVDSCR XViD-KiNGDOM v2.srt
Skipping file: Grown Ups 2010 DVDSCR XViD-KiNGDOM v2.srt as all values in the 'speaker' column are NA's.
Processing file: Grudge.Match.2013.720p.BluRay.srt
Processing file: Guardians.of.the.Galaxy.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Gullivers Travels (2010).720p.En.Hi.srt
Processing file: Hacksaw.Ridge.2016.720p.BluRay.srt
Skipping file: Hacksaw.Ridge.2016.720p.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: Hairspray_.srt
Skipping file: Hairspray_.srt as all values in the 'speaker' column are NA's.
Processing file: Hall Pass (2011) DVDRip XviD-MAXSPEED-EN-HI.srt
Processing file: Halloween-Resurrection.EN.srt
Skipping file: Halloween-Resurrection.EN.srt as all values in the 'speaker' column are NA's.
Processing file: Halloween.2018.HC.1080p.HDRip.X264.AC3-EVO-HI.srt
Processing file: Halloween.II.UNRATED.DVDRip.XviD-ARROW.srt
Processing file: Halloween[2007][Eng][Dvdrip].srt
Skipping file: Halloween[2007][Eng][Dvdrip].srt as all values in the 'speaker' column are NA's.
Processing file: Hancock [2008]DvDrip R5[Eng]-NikonXp.srt
Processing file: Hannah.Montana.and.Miley.Cyrus.Best.of.Both.Worlds.Concert.2008.WEB-DL.DSNP.srt
Skipping file: Hannah.Montana.and.Miley.Cyrus.Best.of.Both.Worlds.Concert.2008.WEB-DL.DSNP.srt as all values in the 'speaker' column are NA's.
Processing file: Hannah.Montana.The.Movie.DVDRip.XviD-NeDiVx.(Hi).srt
Skipping file: Hannah.Montana.The.Movie.DVDRip.XviD-NeDiVx.(Hi).srt as all values in the 'speaker' column are NA's.
Processing file: Hanna[2011]DVDRip[Eng]-FXG.HI.srt
Processing file: Hannibal.Rising.UNRATED.2007.720p.BluRay.x264.DTS-WiKi.eng.srt
Processing file: Hannibal.srt
Processing file: Hansel & Gretel Witch Hunters.[2013].DVDRIP.DIVX.srt
Skipping file: Hansel & Gretel Witch Hunters.[2013].DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Happy.Death.Day.2U.2019.1080p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: Hardball.2001.WEBRip.x264-RARBG.sdh.eng.srt
Skipping file: Hardball.2001.WEBRip.x264-RARBG.sdh.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Harold and Kumar Escape from Guantanimo Bay[2008]DvdRip.avi[weezil420].srt
Skipping file: Harold and Kumar Escape from Guantanimo Bay[2008]DvdRip.avi[weezil420].srt as all values in the 'speaker' column are NA's.
Processing file: Harold.and.Kumar.Go.to.White.Castle.2004.720p.BluRay.AC3.x264-NCmt.eng.sdh.srt
Processing file: Harriet.2019.720P.DVDScr.X264.AC3.HQ.srt
Processing file: Harry Potter And The Chamber Of Secrets_EE_enHI.srt
Processing file: Harry Potter and the Goblet of Fire (Harry Potter IV)(2005) 23.976 ftp-157.06 min-Hi.srt
Processing file: Harry.Potter.and.the.Deathly.Hallows.Part.1.2010.BluRay.720p.DTS.x264-CHD.eng.srt
Processing file: Harry.Potter.And.The.Deathly.Hallows.Part.2.2011.1080p.BrRip.264.YIFY.srt
Processing file: Harry.Potter.And.The.Half.Blood.Prince.2009.DvDRip-FxM.srt
Processing file: Harry.Potter.And.The.Prisoner.Of.Azkaban.2004.1080p.BluRay.H264.AAC-RARBG-eng.srt
Processing file: Harsh.Times[2005]DvDrip[Eng]-aXXo.HI.srt
Processing file: Haywire.2011.1080p.Blu-Ray.AVC.DTS-HD.MA.5.1-HDChina.english.srt
Processing file: Head.Of.State.2003.1080p.WEBRip.x264-RARBG.srt
Processing file: Head_Over_Heels-ENG.srt
Skipping file: Head_Over_Heels-ENG.srt as all values in the 'speaker' column are NA's.
Processing file: Hearin impaired_Pirates.Of.The.Caribbean-At.Worlds.End[2007]DvDrip[Eng]-aXXo.srt
Skipping file: Hearin impaired_Pirates.Of.The.Caribbean-At.Worlds.End[2007]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Hearts.in.Atlantis.2001.1080p.AMZN.WEBRip.DD5.1.x264-ABM.srt
Skipping file: Hearts.in.Atlantis.2001.1080p.AMZN.WEBRip.DD5.1.x264-ABM.srt as all values in the 'speaker' column are NA's.
Processing file: Heaven.Is.For.Real.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Heist.2001.1080p.BluRay.H264.srt
Processing file: Held.Up.1999.1080p.AMZN.WEBRip.DD+5.1.x264-monkee.sdh.eng.srt
Processing file: Hell.Fest.2018.1080p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Hellboy.2004.REMASTERED.720p.BluRay.x264-HD4U-HI.srt
Processing file: Hellboy.2019.V2.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Hellboy.II.The.Golden.Army.2008.BluRay.1080p.DTS.x264.dxva-EuReKA.ENG_HI.srt
Processing file: Hercules.2014.EXTENDED.720p.BluRay.X264-AMIABLE.srt
Processing file: Hercules.Reborn.2014.720p.BluRay.x264.YIFY.srt
Processing file: Here.comes.the.boom.2012.720p.bluray.x264-blow.srt
Processing file: Hereditary.2018.NEW.HDCAM.XViD.AC3-ETRG-HI.srt
Processing file: Hidalgo - English (29_970FPS).srt
Processing file: High.Crimes.2002.720p.BluRay.x264-GAnGSteR. English.srt
Processing file: High.School.Musical.3-Senior.Year[2008]DvDrip-aXXo.en.HI.srt
Skipping file: High.School.Musical.3-Senior.Year[2008]DvDrip-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Highlander IV - Endgame.srt
Skipping file: Highlander IV - Endgame.srt as all values in the 'speaker' column are NA's.
Processing file: high_fidelity_engl.srt
Skipping file: high_fidelity_engl.srt as all values in the 'speaker' column are NA's.
Processing file: hiSpanglish.2004.COMPLETE.BLURAY-COASTER.srt
Processing file: Hit.and.Run.2012.1080p.WEB-DL.DD5.1.H.264-CrazyHDSource.srt
Processing file: Hitch 2005 1080p Blu-ray Remux MPEG-2 DTS-HD MA 5.1 - KRaLiMaRKo_EN.SDH.srt
Processing file: Hitman.Agent.47.2015.720p.BluRay.x264-DRONES.HI.srt
Processing file: Hitman.srt
Skipping file: Hitman.srt as all values in the 'speaker' column are NA's.
Processing file: hiVanilla.Sky.2001.BluRay.1080p.10bit.5.1.x265.HEVC-Qman.UTR.srt
Processing file: HOLES - Closed Caption - English.srt
Processing file: Hollywood Homicide_eng_SDH.srt
Processing file: Hollywood.Ending.(2002).DVDRip.DivX5.[sharethefiles.com].en.srt
Skipping file: Hollywood.Ending.(2002).DVDRip.DivX5.[sharethefiles.com].en.srt as all values in the 'speaker' column are NA's.
Processing file: Holmes.and.Watson.2018.HDCAM.HI.eng.srt
Processing file: Homefront.2013.720p.BluRay.X264-SPARKS-SDH.srt
Processing file: Hoot.2006.1080p.WEBRip.srt
Skipping file: Hoot.2006.1080p.WEBRip.srt as all values in the 'speaker' column are NA's.
Processing file: Hope.Springs.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: Horrible.Bosses.2.2014.720p.BluRay.x264-SPARKS.srt
Text not found in sentences: But then when Dad called the cops and proved he doesn't give a fuck about me... ...
Processing file: horrible.bosses.2011.dvdrip.xvid-amiable.eng.HI.srt
Processing file: Hostage.srt
Skipping file: Hostage.srt as all values in the 'speaker' column are NA's.
Processing file: HOSTEL 2005 - ITA - Horror - DVD RIP - XviD - by ILE 66.srt
Skipping file: HOSTEL 2005 - ITA - Horror - DVD RIP - XviD - by ILE 66.srt as all values in the 'speaker' column are NA's.
Processing file: Hot.Pursuit.2015.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Hot.Tub.Time.Machine.2.2015.UNRATED.HDRip.XViD-ETRG.srt
Skipping file: Hot.Tub.Time.Machine.2.2015.UNRATED.HDRip.XViD-ETRG.srt as all values in the 'speaker' column are NA's.
Processing file: Hot.Tub.Time.Machine.UNRATED.DVDRip.srt
Processing file: Hotel.Artemis.2018.720p.BluRay.x264-Replica-HI.srt
Skipping file: Hotel.Artemis.2018.720p.BluRay.x264-Replica-HI.srt as all values in the 'speaker' column are NA's.
Processing file: House of Wax 2005 BluRay 1080p AVC DTS-HD MA 5.1-TRiToN.srt
Skipping file: House of Wax 2005 BluRay 1080p AVC DTS-HD MA 5.1-TRiToN.srt as all values in the 'speaker' column are NA's.
Processing file: house.at.the.end.of.the.street.2012.720p.bluray.x264-sparks.eng.HI.srt
Processing file: House.of.1000.Corpses.2003.1080p.BluRay.x264-PUZZLE.srt
Processing file: House.Of.The.Dead.[2003].DVDRip.XviD-BLiTZKRiEG.srt
Skipping file: House.Of.The.Dead.[2003].DVDRip.XviD-BLiTZKRiEG.srt as all values in the 'speaker' column are NA's.
Processing file: How the Grinch Stole Christmas.[2000].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: How the Grinch Stole Christmas.[2000].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: How to Be a Latin Lover (2017) 720p.BluRay.x264-DRONES.srt
Skipping file: How to Be a Latin Lover (2017) 720p.BluRay.x264-DRONES.srt as all values in the 'speaker' column are NA's.
Processing file: How.High.2001.720p.WEBRip.x264-[YTS.AM].Hi.srt
Skipping file: How.High.2001.720p.WEBRip.x264-[YTS.AM].Hi.srt as all values in the 'speaker' column are NA's.
Processing file: How.to.Lose.a.Guy.in.10.Days.2003.BluRay.1080p.TrueHD.5.1.AVC.REMUX-FraMeSToR_EN.SDH.srt
Processing file: Hugo 2011.720p.BrRip.X264.YIFY.srt
Skipping file: Hugo 2011.720p.BrRip.X264.YIFY.srt as all values in the 'speaker' column are NA's.
Processing file: Hulk[2003]DvDrip-aXXo.srt
Processing file: Hunter.Killer.2018.HC.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Hustlers.2019.720p.HDCAM-GETB8-HI.srt
Skipping file: Hustlers.2019.720p.HDCAM-GETB8-HI.srt as all values in the 'speaker' column are NA's.
Processing file: I Am Number Four 2011 720p BRRip x264 RmD (HDScene Release).srt
Skipping file: I Am Number Four 2011 720p BRRip x264 RmD (HDScene Release).srt as all values in the 'speaker' column are NA's.
Processing file: I can do bad all by myself. The play (2009) Eng.srt
Skipping file: I can do bad all by myself. The play (2009) Eng.srt as all values in the 'speaker' column are NA's.
Processing file: I Dont Know How She Does It 2011 DVDRip XviD- AMIABLE HI.srt
Skipping file: I Dont Know How She Does It 2011 DVDRip XviD- AMIABLE HI.srt as all values in the 'speaker' column are NA's.
Processing file: I Spy - English Hearing Impaired (25FPS).srt
Processing file: i-prom.sdh.srt
Processing file: I.Am.Legend.2007.Alternate.Ending.1080p.BluRay.x264.anoXmous_eng.srt
Processing file: I.Can.Only.Imagine.2018.HDCAM.ENG.X264.HQMic-SugarTits-HI.srt
Skipping file: I.Can.Only.Imagine.2018.HDCAM.ENG.X264.HQMic-SugarTits-HI.srt as all values in the 'speaker' column are NA's.
Processing file: I.Dreamed.of.Africa.2000.WEBRip.x264-ION10.srt
Processing file: I.Feel.Pretty.2018.1080p.WEB-DL.H264.AC3-EVO-ENGLISH.srt
Processing file: I.Frankenstein.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: I.Love.You.Beth.Cooper.DVDRip.XviD-DiAMOND.Hi.srt
Processing file: I.Love.You.Man.2009.WEBRip.Amazon.srt
Processing file: I.Now.Pronounce.You.Chuck.and.Larry.2006.1080p.BluRay.H264.AAC-RARBG.srt
Processing file: I.Robot.2004.1080p.Bluray.x264.DTS-DEFiNiTE.srt
Processing file: Ice Princess_2005_ENG.srt
Skipping file: Ice Princess_2005_ENG.srt as all values in the 'speaker' column are NA's.
Processing file: Identity.Thief.2013.UNRATED.720p.WEBRiP.XViD.AC3-LEGi0N_Subtitle - English.srt
Processing file: If.I.Stay.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Imagine That.[2009].PREMIERE.DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Imagine That.[2009].PREMIERE.DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: imbt-xvid-jj-cd1.en.HI.srt
Processing file: imbt-xvid-jj-cd2.en.HI.srt
Text not found in sentences: And Aunt Jessie's cousin Dorrie in Abilene, the one with the husband who won
the pie-eating contest and is a crossword puzzle nut, they have a subscription to The New York Times.
 
Processing file: Immortals.2011.720p.BluRay.x264.DTS-HDChina.English.srt
Processing file: Impostor.2001.1080p.BluRay.DTS.x264-hd4u-SDH.srt
Processing file: In.the.Land.of.Women.2007.1080p.WEBRip.x264-RARBG SDH.srt
Skipping file: In.the.Land.of.Women.2007.1080p.WEBRip.x264-RARBG SDH.srt as all values in the 'speaker' column are NA's.
Processing file: In.the.Name.of.the.King.A.Dungeon.Siege.Tale.2007.DVDRiP-SUNSPOT.1.srt
Skipping file: In.the.Name.of.the.King.A.Dungeon.Siege.Tale.2007.DVDRiP-SUNSPOT.1.srt as all values in the 'speaker' column are NA's.
Processing file: In.the.Name.of.the.King.A.Dungeon.Siege.Tale.2007.DVDRiP-SUNSPOT.2.srt
Skipping file: In.the.Name.of.the.King.A.Dungeon.Siege.Tale.2007.DVDRiP-SUNSPOT.2.srt as all values in the 'speaker' column are NA's.
Processing file: In.Time.2011.720p.Bluray.x264.YIFY.srt
Processing file: Incarnate.2016.720p.BluRay.x264-PFa-HI.srt
Processing file: Inception.2010.DVDRip.XviD.AC3-ViSiON.srt
Processing file: Indiana.Jones.And.The.Kingdom.Of.The.Crystal.Skull[2008]DvDrip-aXXo.en.HI.srt
Processing file: Indivisible.2018.720p.BluRay.x264-GECKOS.srt
Processing file: Inferno.2016.720p.HC.HDRip.X264.AC3-EVO.srt
Skipping file: Inferno.2016.720p.HC.HDRip.X264.AC3-EVO.srt as all values in the 'speaker' column are NA's.
Processing file: Ing.srt
Skipping file: Ing.srt as all values in the 'speaker' column are NA's.
Processing file: Inglourious.Basterds.2009.DvDRip-FxM.en.HI.srt
Processing file: Inside.Man.2006.DVDRip.XviD-UnSeeN.srt
Processing file: Insidious.2010.720p.BrRip.x264.srt
Skipping file: Insidious.2010.720p.BrRip.x264.srt as all values in the 'speaker' column are NA's.
Processing file: Insidious.Chapter.2.2013.720p.BluRay.srt
Processing file: Insidious.Chapter.3.2015.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Insidious.The.Last.Key.2018.HC.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Insomnia.2002.1080p.BluRay.DTS.x264-CtrlHD.ENG_HI.srt
Processing file: Instant.Family.2018.1080p.WEB-DL.X264.AC3-SeeHD-HI.srt
Skipping file: Instant.Family.2018.1080p.WEB-DL.X264.AC3-SeeHD-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Insurgent.2015.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Interstellar.2014.720p.BluRay.x264-DAA-HI.srt
Processing file: into.the.blue.2005.bluray.remux.1080p.mpeg-2.dts-hd.ma.5.1.SDH.srt
Processing file: Into.The.Storm.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Into.the.Woods.2014.DVDSCR.X264-PLAYNOW.srt
Processing file: Intolerable Cruelty.srt
Skipping file: Intolerable Cruelty.srt as all values in the 'speaker' column are NA's.
Processing file: invincible dvd rip.srt
Processing file: Iron Man 3[2013]BRRip XviD[AC3]-ETRG.srt
Processing file: Iron.Man.2.2010.BluRay.1080p.DTS-HD.x264-Grym.srt
Processing file: Iron.Man[2008]DvDrip-aXXo.en.HI.srt
Processing file: Isnt.It.Romantic.2019.720p.NF.WEB-DL.DD5.1.H264-CMRG-HI.srt
Skipping file: Isnt.It.Romantic.2019.720p.NF.WEB-DL.DD5.1.H264-CMRG-HI.srt as all values in the 'speaker' column are NA's.
Processing file: It.Chapter.Two.2019.720p.HC.HDRip.900MB.x264-GalaxyRG-HI.srt
Skipping file: It.Chapter.Two.2019.720p.HC.HDRip.900MB.x264-GalaxyRG-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Its Complicated.2009.DvdScr.Xvid {1337x}-Noir.srt
Text not found in sentences: Mom, She'll be there in a couple of hours.
 
Processing file: Its Kind Of A Funny Story (2010).720p.En.srt
Processing file: J.Edgar.2011.480p.BRRiP.XViD.AC3-LEGi0N_Subtitle - English.srt
Processing file: Jack And Jill 2011 720p BluRay x264 DTS-HDChina.English.srt
Processing file: Jack.Reacher.2012.720p.BluRay.X264-AMIABLE.srt
Processing file: Jack.Reacher.Never.Go.Back.2016.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Jackass.Presents.Bad.Grandpa.2013.UNRATED.720p.BluRay.x264-BLOW.srt
Processing file: James.Bond.Die.Another.Day.2002.1080p.BRrip.x264.YIFY.ENG.srt
Processing file: Jarhead.srt
Skipping file: Jarhead.srt as all values in the 'speaker' column are NA's.
Processing file: Jason.X.2001.1080p.BluRay.x264-LiViDiTY.Hi.srt
Processing file: Jay.And.Silent.Bob.Strike.Back.2001.1080p.BluRay.x264-HDMI.eng.srt
Processing file: jck3-provoke.srt
Skipping file: jck3-provoke.srt as all values in the 'speaker' column are NA's.
Processing file: Jeepers.Creepers.2001.REMASTERED.720p.BluRay.X264-AMIABLE-HI.srt
Processing file: Jeepers.Creepers.II.2003.720p.BluRay.DTS.x264-PublicHD.srt
Processing file: Jem.and.the.Holograms.2015.V2.HC.HDRip.XviD.AC3-EVO.HI.srt
Processing file: Jennifers.Body.UNRATED.2009.1080p.BrRip.x264..srt
Skipping file: Jennifers.Body.UNRATED.2009.1080p.BrRip.x264..srt as all values in the 'speaker' column are NA's.
Processing file: Jersey Girl.srt
Skipping file: Jersey Girl.srt as all values in the 'speaker' column are NA's.
Processing file: Jersey.Boys.2014.720p.BluRay.srt
Processing file: Jexi.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: jm.dvdrip.xvid-deity_english_no_italic.srt
Skipping file: jm.dvdrip.xvid-deity_english_no_italic.srt as all values in the 'speaker' column are NA's.
Processing file: jmj-shorts.en.HI.srt
Processing file: Jobs.2013.720p.BluRay.srt
Processing file: Joe Dirt 2001 1080p Blu-ray Remux AVC DTS-HD MA 5.1 - KRaLiMaRKo.en.sdh.srt
Processing file: Joe.Somebody.DVDRip.DivX-DVL.srt
Skipping file: Joe.Somebody.DVDRip.DivX-DVL.srt as all values in the 'speaker' column are NA's.
Processing file: John Q. (2002) 1080p.BluRay.x264-RETREAT.srt
Processing file: John.Carter.2012.720p.BluRay.x264.DTS-HDChina.english.srt
Processing file: John.Tucker.Must.Die.DVDRip.XViD-ALLiANCE.srt
Processing file: John.Wick.2014.720p.BluRay.srt
Processing file: John.Wick.3.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: John.Wick.Chapter.2.2017.720p.BluRay.x264-SPARKS.HI.srt
Skipping file: John.Wick.Chapter.2.2017.720p.BluRay.x264-SPARKS.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Johnny.English.Reborn.BDRip.XviD-DoNE.Hi.srt
Processing file: Johnny.English.Strikes.Again.2018.720p.BluRay.x264.DTS-FGT-HI.srt
Processing file: johnson.family.vacation.2004.720p.bluray.x264-veto HI.srt
Skipping file: johnson.family.vacation.2004.720p.bluray.x264-veto HI.srt as all values in the 'speaker' column are NA's.
Processing file: Joker.2019.HC.1080p.HDRip.X264.AC3-EVO-HI.srt
Skipping file: Joker.2019.HC.1080p.HDRip.X264.AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Jonah Hex.[2010].DVDRIP.DIVX.[Eng]-DUQA.srt
Processing file: josie_and_the_pussycats_2001.srt
Skipping file: josie_and_the_pussycats_2001.srt as all values in the 'speaker' column are NA's.
Processing file: Journey.2.The.Mysterious.Island.2012.720p.BluRay.x264.DTS.AC3.Dual.Audio-HDChina.english.srt
Processing file: Journey.To.The.Center.Of.The.Earth[2008]DvDrip-aXXo.en.HI.srt
Processing file: Joy Ride 2001 BRRip 480p x264 AAC - VYTO.srt
Processing file: Joyful.Noise.2012.DVDRip.srt
Processing file: Judy Moody And The Not Bummer Summer (2011) English for hearing-impaired.srt
Processing file: Jumanji-Copy1.The.Next.Level.2019.HC.720p.HDRip.800MB.x264-GalaxyRG-HI.srt
Processing file: Jumper[2008]DvDrip.AC3-aXXo.en.HI.srt
Skipping file: Jumper[2008]DvDrip.AC3-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Jumping.the.Broom.WEBRip.Netflix.en[cc].srt
Skipping file: Jumping.the.Broom.WEBRip.Netflix.en[cc].srt as all values in the 'speaker' column are NA's.
Processing file: Jupiter.Ascending.2015.720p.BluRay.x264-SPARKS.srt
Processing file: Jurassic Park III English (Hearing Impaired).srt
Processing file: Jurassic.World.2015.720p.BluRay.srt
Processing file: Jurassic.World.2018.720p.WEB-DL.H264.srt
Processing file: Just.Go.With.It.2011.720p.BluRay.srt
Processing file: Just.Like.Heaven.2005.WEBRip.AMZN.en.srt
Processing file: Just.Married.DVDRiP.XViD-DcN.srt
Skipping file: Just.Married.DVDRiP.XViD-DcN.srt as all values in the 'speaker' column are NA's.
Processing file: Just.My.Luck.DVDRip.XviD-DiAMOND.srt
Skipping file: Just.My.Luck.DVDRip.XviD-DiAMOND.srt as all values in the 'speaker' column are NA's.
Processing file: Just.Visiting.2001.720p.BluRay.x264-NOSCREENS-HI.srt
Processing file: Justice.League.2017.1080p.WEBRip.x264.AAC2.0-SHITBOX.HI.srt
Processing file: JUSTIN BIEBER-NEVER SAY NEVER [2011] DVD Rip Xvid [StB].srt
Processing file: K-19.The.Widowmaker.2002.1080p.BluRay.REMUX.AVC.TrueHD.5.1-EPSiLON.English.srt
Processing file: K-pax_eng.srt
Skipping file: K-pax_eng.srt as all values in the 'speaker' column are NA's.
Processing file: Keeping.the.Faith.2000.720p.BluRay.X264-AMIABLE.srt
Processing file: Keeping.Up.With.The.Joneses.2016.720p.BluRay.x264-DRONES-HI.srt
Processing file: Kevin Smith - Clerks II (2006) DVDRip XviD AC3 JUPiT Cd1.Eng2HI.srt
Processing file: Kevin Smith - Clerks II (2006) DVDRip XviD AC3 JUPiT Cd2.Eng2HI.srt
Processing file: Kevin Smith - Clerks II (2006) DVDRip XviD AC3 JUPiT.Eng2HI.srt
Processing file: Kevin.Hart.Let.Me.Explain.WEBRip.Netflix.en[cc].srt
Processing file: Kevin.Hart.What.Now.2016.720p.BluRay.x264-GECKOS.sdh.srt
Text not found in sentences: He goes, "Dad, it's real dark outside.
 
Processing file: Kick-Ass.2.2013.720p.BluRay.x264-VeDeTT.srt
Processing file: Kick.Ass.2010.R5.AC3.XViD-Rx.srt
Skipping file: Kick.Ass.2010.R5.AC3.XViD-Rx.srt as all values in the 'speaker' column are NA's.
Processing file: kicking and screaming.srt
Skipping file: kicking and screaming.srt as all values in the 'speaker' column are NA's.
Processing file: kid.srt
Skipping file: kid.srt as all values in the 'speaker' column are NA's.
Processing file: Kids In America 2005.srt
Skipping file: Kids In America 2005.srt as all values in the 'speaker' column are NA's.
Processing file: Kill Bill - Volume 1.srt
Skipping file: Kill Bill - Volume 1.srt as all values in the 'speaker' column are NA's.
Processing file: Kill.Bill.Vol.2.2004.720p.BrRip.x264.YIFY.HI.srt
Skipping file: Kill.Bill.Vol.2.2004.720p.BrRip.x264.YIFY.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Killers R5 perfection.srt
Skipping file: Killers R5 perfection.srt as all values in the 'speaker' column are NA's.
Processing file: Killing Them Softly.[2012].UNRATED.DVDRIP.DIVX.srt
Skipping file: Killing Them Softly.[2012].UNRATED.DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Kin.2018.720p.HDCAM.X264-24HD-HI.srt
Processing file: King Arthur Legend of the Sword 2017.srt
Skipping file: King Arthur Legend of the Sword 2017.srt as all values in the 'speaker' column are NA's.
Processing file: King.Kong.2005.EXTENDED.DVDRip.XviD-SAiNTS.CD1INGLES.srt
Skipping file: King.Kong.2005.EXTENDED.DVDRip.XviD-SAiNTS.CD1INGLES.srt as all values in the 'speaker' column are NA's.
Processing file: King.Kong.2005.EXTENDED.DVDRip.XviD-SAiNTS.CD2ingles.srt
Skipping file: King.Kong.2005.EXTENDED.DVDRip.XviD-SAiNTS.CD2ingles.srt as all values in the 'speaker' column are NA's.
Processing file: Kingdom of Heaven_cd1_en.srt
Skipping file: Kingdom of Heaven_cd1_en.srt as all values in the 'speaker' column are NA's.
Processing file: Kingdom of Heaven_cd2_en.srt
Skipping file: Kingdom of Heaven_cd2_en.srt as all values in the 'speaker' column are NA's.
Processing file: Kings ransom English.srt
Skipping file: Kings ransom English.srt as all values in the 'speaker' column are NA's.
Processing file: Kingsman.The.Secret.Service.2014.1080p.WEB-DL.DD5.1.H264-RARBG.srt
Processing file: Kiss.Of.The.Dragon.2001.1080p.BluRay.x264-.YTS.AM.srt
Skipping file: Kiss.Of.The.Dragon.2001.1080p.BluRay.x264-.YTS.AM.srt as all values in the 'speaker' column are NA's.
Processing file: Knight and Day.[2010].R5.DVDRIP.H264.[Eng].DUQA.srt
Skipping file: Knight and Day.[2010].R5.DVDRIP.H264.[Eng].DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Knives.Out.2019.720p.WEBRip.x264.AAC-.YTS.MX.srt
Skipping file: Knives.Out.2019.720p.WEBRip.x264.AAC-.YTS.MX.srt as all values in the 'speaker' column are NA's.
Processing file: Knocked.Up.2007.1080p.HDDVD.DTS.x264-HDV.ENG_HI.srt
Processing file: knowing-h.srt
Processing file: Kong.Skull.Island.2017.720p.BluRay.x264-SPARKS.HI.srt
Processing file: kung pow dvl eng.srt
Skipping file: kung pow dvl eng.srt as all values in the 'speaker' column are NA's.
Processing file: l-allaboutsteve.en.HI.srt
Skipping file: l-allaboutsteve.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Labor.Day.2013.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Ladder 49[2004]DVDRip[Xvid AC3[5.1][ENG]-RoCK&BlueLadyRG.srt
Skipping file: Ladder 49[2004]DVDRip[Xvid AC3[5.1][ENG]-RoCK&BlueLadyRG.srt as all values in the 'speaker' column are NA's.
Processing file: Lady in the Water (2006) [1080p BluRay x265 10bit Tigole].SDH.eng.srt
Processing file: Lakeview.Terrace.720p.Bluray.x264-SEPTiC-sdh.srt
Processing file: Land.of.the.Lost[2009]DvDrip-aXXo.srt
Processing file: Lara Croft Tomb Raider 2001 720p BluRay DTS x264-RightSiZE.SDH.srt
Processing file: Lara Croft Tomb Raider_The Cradle of Life Cd 1_ENG.srt
Skipping file: Lara Croft Tomb Raider_The Cradle of Life Cd 1_ENG.srt as all values in the 'speaker' column are NA's.
Processing file: Lara Croft Tomb Raider_The Cradle of Life Cd 2_ENG.srt
Skipping file: Lara Croft Tomb Raider_The Cradle of Life Cd 2_ENG.srt as all values in the 'speaker' column are NA's.
Processing file: Larry.Crowne.BDRip.XviD-DoNE.Hi.srt
Skipping file: Larry.Crowne.BDRip.XviD-DoNE.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Last dance.srt
Skipping file: Last dance.srt as all values in the 'speaker' column are NA's.
Processing file: Last Holiday 2006 1080p BluRay.eng.SDH.srt
Processing file: Last.Christmas.2019.HC.1080p.HDRip.srt
Processing file: Last.Vegas.2013.1080p.BluRay.x264-SPARKS-sdh.srt
Processing file: Law.Abiding.Citizen.720p.BrRip.450MB.YIFY.srt
Skipping file: Law.Abiding.Citizen.720p.BrRip.450MB.YIFY.srt as all values in the 'speaker' column are NA's.
Processing file: Lawless.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: Leap.Year.REPACK.BDRip.srt
Processing file: Leatherheads[2008]DvDrip-aXXo.en.HI.srt
Processing file: Legally.Blonde.2001.1080p.BrRip.x264.YIFY.srt
Processing file: Legend of Zorro_ The (2005).srt
Processing file: Legion.2010.1080p.BrRip.x264.YIFY.srt
Skipping file: Legion.2010.1080p.BrRip.x264.YIFY.srt as all values in the 'speaker' column are NA's.
Processing file: Lemony Snickets A Series of Unfortunate Events.[2004].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Lemony Snickets A Series of Unfortunate Events.[2004].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Les.Miserables.2012.720p.BluRay.x264-SPARKS.srt
Processing file: Let Me In (2010).Vision.En.srt
Skipping file: Let Me In (2010).Vision.En.srt as all values in the 'speaker' column are NA's.
Processing file: Lets.Be.Cops.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Lets.Go.to.Prison.2006.1080p.WEBRip.x264-RARBG.srt
Processing file: Letters To God (2010).Kingdom.En.Hi.srt
Skipping file: Letters To God (2010).Kingdom.En.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Letters.To.Juliet.2010.720p.BluRay.x264-Felony.srt
Skipping file: Letters.To.Juliet.2010.720p.BluRay.x264-Felony.srt as all values in the 'speaker' column are NA's.
Processing file: Life As We Know It (2010) Z1.EN.srt
Processing file: Life of Pi.[2012].RETAIL.DVDRIP.DIVX.srt
Skipping file: Life of Pi.[2012].RETAIL.DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Life.2017.720p.BluRay.x264-Replica-HI.srt
Processing file: Life.Itself.2018.1080p.WEB-DL.H264.AC3-EVO-HI.srt
Skipping file: Life.Itself.2018.1080p.WEB-DL.H264.AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Life.of.the.Party.2018.1080p.WEB-DL.H264.AC3-EVO.srt
Processing file: Like Mike[2002]DVDRip[Eng] -alwaysontop.srt
Skipping file: Like Mike[2002]DVDRip[Eng] -alwaysontop.srt as all values in the 'speaker' column are NA's.
Processing file: Limitless.2011.Unrated.Extended.Cut.720p.BluRay.x264.DTS-HDChina.english.srt
Skipping file: Limitless.2011.Unrated.Extended.Cut.720p.BluRay.x264.DTS-HDChina.english.srt as all values in the 'speaker' column are NA's.
Processing file: Lions.For.Lambs.2007.1080p.BluRay.DTS..x264-Spekt0r.srt
Processing file: Little Fockers (2010).Defaced.Hi.En.srt
Text not found in sentences: I understand, Nurse Focker.
 
Text not found in sentences: Mom, Pam and I are fine.
 
Text not found in sentences: Dad stuck Grandpa Jack in the wee-wee last night.
 
Text not found in sentences: Dad stuck Grandpa Jack in the wee-wee last night.
 
Text not found in sentences: My Grandpa Bernie taught me this.
 
Text not found in sentences: Dad, I got to go!
 
Processing file: Little Nicky English subs.srt
Processing file: Little.2019.720p.BluRay.x264-DRONES-HI.srt
Processing file: Little.Black.Book.2004.WEBRip.x264-ION10.srt
Processing file: Little.Boy.2015.720p.BluRay.x264-GECKOS-RARBG_EVO_ETRG_PLAYNOW.srt
Processing file: Little.Women.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Live Free or Die Hard 4.srt
Skipping file: Live Free or Die Hard 4.srt as all values in the 'speaker' column are NA's.
Processing file: lmg-shutter.en.HI.srt
Skipping file: lmg-shutter.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Logan.2017.720p.BluRay-CHI.srt
Processing file: London.Fields.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Long.Shot.2019.720p.srt
Processing file: Looper.2012.OFFICIAL.TRAILER.srt
Skipping file: Looper.2012.OFFICIAL.TRAILER.srt as all values in the 'speaker' column are NA's.
Processing file: Lord.Of.War.2005.BRRip.XviD.AC3-D-Z0N3.srt
Skipping file: Lord.Of.War.2005.BRRip.XviD.AC3-D-Z0N3.srt as all values in the 'speaker' column are NA's.
Processing file: Loser.2000.1080p.WEBRip.x264.AAC5.1-[YTS.MX].srt
Processing file: Love Actually DVDRip Dual AC3 Spanish English Pj.eng.srt
Skipping file: Love Actually DVDRip Dual AC3 Spanish English Pj.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Love And Other Drugs-2010-DVDRIP.Hi.srt
Processing file: Love.and.Basketball.2000.1080p.BluRay.X264-AMIABLE.HI.eng.srt
Processing file: Love.Simon.2018.720p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: Lucky Number Slevin.srt
Processing file: Lucky Numbers.srt
Skipping file: Lucky Numbers.srt as all values in the 'speaker' column are NA's.
Processing file: Lucky.You.2007.1080p.WEBRip.x264.srt
Processing file: Lucy.2014.720p.BluRay.srt
Processing file: m-tfk-720p.eng.srt
Processing file: Ma.2019.720p.WEBRip.x264-YIFY-HI.srt
Processing file: Machete.2010.720p.BRRip.XviD.AC3-FLAWL3SS.srt
Skipping file: Machete.2010.720p.BRRip.XviD.AC3-FLAWL3SS.srt as all values in the 'speaker' column are NA's.
Processing file: Machete.Kills.2013.1080p.BluRay.x264-SPARKS-sdh.srt
Processing file: Mad Money[2008]DvDrip AC3[Eng]-FXG.en.HI.srt
Skipping file: Mad Money[2008]DvDrip AC3[Eng]-FXG.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Mad.Max.Fury.Road.2015.720p.BluRay.srt
Processing file: Magic Mike XXL 2015 720p WEB-DL X264 AC3-EVO.srt
Processing file: Magic Mike[2012]BRRip XviD-ETRG.srt
Processing file: Maid.In.Manhattan.2002.BluRay.x265-RARBG.en.srt
Skipping file: Maid.In.Manhattan.2002.BluRay.x265-RARBG.en.srt as all values in the 'speaker' column are NA's.
Processing file: Maleficent (2014) Decorate.srt
Skipping file: Maleficent (2014) Decorate.srt as all values in the 'speaker' column are NA's.
Processing file: Maleficent Mistress of Evil.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Malibus.Most.Wanted.2003.720p.WEBRip.x264.AAC-[YTS.MX].srt
Processing file: Mamma.Mia.Here.We.Go.Again.2018.720p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: Man.Of.Steel.2013.720p.BluRay.x264-Felony.srt
Processing file: Man.Of.The.Year.2006.1080p.WEBRip.x264-RARBG.srt
Skipping file: Man.Of.The.Year.2006.1080p.WEBRip.x264-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: Man.on.a.Ledge.2012.PROPER.DVDRip.XviD-SPARKS.english.srt
Processing file: Man.On.Fire.2004.720p.BluRay.x264.YIFY.srt
Skipping file: Man.On.Fire.2004.720p.BluRay.x264.YIFY.srt as all values in the 'speaker' column are NA's.
Processing file: Marley & Me[2008]DvDrip[Eng]-FXG.srt
Skipping file: Marley & Me[2008]DvDrip[Eng]-FXG.srt as all values in the 'speaker' column are NA's.
Processing file: Marmaduke 2010 720p BluRay x264-AVS720.srt
Skipping file: Marmaduke 2010 720p BluRay x264-AVS720.srt as all values in the 'speaker' column are NA's.
Processing file: Mary.Poppins.Returns.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: Master.and.Commander.2003.720p.BRRip.XviD.AC3-FLAWL3SS.srt
Skipping file: Master.and.Commander.2003.720p.BRRip.XviD.AC3-FLAWL3SS.srt as all values in the 'speaker' column are NA's.
Processing file: Masterminds.2016.720p.BluRay.X264-AMIABLE.HI.srt
Processing file: Matchstick.Men.2003.720p.BluRay.x264-HD4U.srt
Processing file: Max.2015.720p.BluRay.x264-DRONES.HI.srt
Processing file: Max.Keebles.Big.Move.DvDivX-TWCiSO.English.Subtitle.srt
Processing file: Max.Steel.2016.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Maze.Runner.The.Death.Cure.2018.720p.BluRay.x264-SPARKS.HI.srt
Processing file: McFarland.USA.2015.WEB-DL.DSNP.srt
Processing file: mean girls 1 special collections.[2004].DVDRIP.DIVX.[Eng]-DUQA.srt
Skipping file: mean girls 1 special collections.[2004].DVDRIP.DIVX.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Meet The Parents.en.srt
Skipping file: Meet The Parents.en.srt as all values in the 'speaker' column are NA's.
Processing file: Meet the Spartans[2008][Unrated Edition]DvDrip[Eng]-FXG.english_HI.srt
Processing file: Meet.Dave.2008.1080p.BluRay.x265-RARBG.srt
Processing file: Meet.The.Fockers.DVDRip.srt
Skipping file: Meet.The.Fockers.DVDRip.srt as all values in the 'speaker' column are NA's.
Processing file: Men.In.Black.3.2012.1080p.BluRay.x264.YIFY.srt
Processing file: Men.In.Black.II.2002.1080p.Blu-ray.AVC.DTS-HD.MA.5.srt
Processing file: Men.in.Black.International.2019.720p.HC.HDRip.x264-MKVCage-HI.srt
Processing file: metis-datenight-720p.srt
Processing file: Me_ Myself And Irene.EN.srt
Processing file: Miami.Vice.2006.1080p.BluRay.x264.YIFY.HI.srt
Processing file: Midsommar.2019.1080p.HC.HDRip.X264.srt
Processing file: Midway.2019.720p.NEW.HD-TS-GETB8-HI.srt
Processing file: Mile.22.2018.720p.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Million.Dollar.Arm.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Mindhunters.srt
Processing file: Minority.Report.2002.720p.BluRay.x264.srt
Processing file: Miracle.At.St.Anna[2008]DvDrip-aXXo.en.HI.srt
Skipping file: Miracle.At.St.Anna[2008]DvDrip-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: miracle.srt
Processing file: Mirror Mirror[2012]BRRip XviD-ETRG-HI.srt
Processing file: Mirrors[2008]DvDrip-aXXo.en.HI.srt
Processing file: Miss.Bala.2019.720p.HDCAM-1XBET-HI.srt
Processing file: Miss.Congeniality.2.Armed.And.Fabulous.2005.1080p.BluRay.x264-MELiTE.ENG_HI.srt
Processing file: Miss.Congeniality.2000.1080p.BluRay.x264-MELiTE.ENG_HI.srt
Processing file: Miss.March.UNRATED.1080p.BluRay.x264-HD1080.srt
Skipping file: Miss.March.UNRATED.1080p.BluRay.x264-HD1080.srt as all values in the 'speaker' column are NA's.
Processing file: Mission.Impossible.3.4K.REMASTERED.2006.GERMAN.DL.AC3D.1080p.BluRay.x265-FuN_Subtitles05.ENG.srt
Processing file: Mission.Impossible.Fallout.2018.720p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Mission.Impossible.II.2000.1080p.BluRay.x264-[YTS.AG].srt
Skipping file: Mission.Impossible.II.2000.1080p.BluRay.x264-[YTS.AG].srt as all values in the 'speaker' column are NA's.
Processing file: Mission.Impossible.Rogue.Nation.2015.BDRip.x264-SPARKS.en.HI.srt
Processing file: MissionToMars-en.srt
Skipping file: MissionToMars-en.srt as all values in the 'speaker' column are NA's.
Processing file: Moms.Night.Out.2014.720p.BluRay.srt
Processing file: Moneyball.2011.BRRip.srt
Processing file: Monte.Carlo.2011.BluRay.720p.DTS.x264-CHD.Hi.srt
Processing file: Mortal.Engines.2018.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Mortdecai.2015.720p.BluRay.srt
Processing file: Movie 43.[2013].UNRATED.DVDRIP.DIVX.srt
Skipping file: Movie 43.[2013].UNRATED.DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Mr Poppers Penguins[2011]BRRip XviD-ExtraTorrentRG.srt
Processing file: Mr. 3000 (2004) 1080p NF.en SDH.srt
Processing file: Mr. Magoriums Wonder Emporium[2007]DvDrip[Eng]-FXG_Eng.srt
Processing file: Mr.&.Mrs.Smith[2005][Unrated.Edition]DvDrip[Eng]-aXXo.srt
Skipping file: Mr.&.Mrs.Smith[2005][Unrated.Edition]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Mr.Brooks[2007]DvDrip[Eng]-aXXo.srt
Skipping file: Mr.Brooks[2007]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Munich.2005.720p.BluRay.x264-AMIABLE-HI.srt
Processing file: Muppets.Most.Wanted.2014.WEB-DL.DSNP.srt
Processing file: Murder.By.Numbers.2002.720p.WEBRip.x264.AAC-[YTS.MX].srt
Processing file: Murder.On.The.Orient.Express.2017.720p.BluRay.x264-SPARKS.HI.srt
Processing file: My Sisters Keeper.[2009].RETAIL.DVDRIP.XVID.[Eng]-DUQA.srt
Processing file: My Soul to Take.Hi.srt
Processing file: My.All.American.2015.720p.BluRay.x264.VPPV.srt
Processing file: my.babys.daddy.dvdrip.xvid-deity.srt
Text not found in sentences: No, Mom . ''
Processing file: My.Best.Friends.Girl.2008.UNRATED.1080p.BulRay.x265-RARBG_HI.srt
Skipping file: My.Best.Friends.Girl.2008.UNRATED.1080p.BulRay.x265-RARBG_HI.srt as all values in the 'speaker' column are NA's.
Processing file: My.Life.in.Ruins.DVDRip.XviD-DiAMOND.srt
Processing file: My.Super.Ex.Girlfriend.2006.720p.BrRip.x264.YIFY.srt
Skipping file: My.Super.Ex.Girlfriend.2006.720p.BrRip.x264.YIFY.srt as all values in the 'speaker' column are NA's.
Processing file: Nacho.Libre.2006.en.srt
Skipping file: Nacho.Libre.2006.en.srt as all values in the 'speaker' column are NA's.
Processing file: Nanny McPhee - English SDH (29_970FPS).srt
Skipping file: Nanny McPhee - English SDH (29_970FPS).srt as all values in the 'speaker' column are NA's.
Processing file: Nanny McPhee and the Big Bang.[2010].DVDRIP.H264.[Eng]-DUQA.srt
Processing file: National treasure.en-HI.srt
Skipping file: National treasure.en-HI.srt as all values in the 'speaker' column are NA's.
Processing file: National.Treasure.2-Book.Of.Secrets[2007]DvDrip[Eng]-aXXo.en.HI.srt
Skipping file: National.Treasure.2-Book.Of.Secrets[2007]DvDrip[Eng]-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: nedivx-everysfine.en.srt
Processing file: nedivx-inkheart-cd1.en.HI.srt
Text not found in sentences: and Uncle Henry and Dorothy could see... ... where the long grass bowed in waves before the coming storm. '
Processing file: nedivx-inkheart-cd2.en.HI.srt
Processing file: Need.For.Speed.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Neighbors.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Never.Back.Down[2008]DvDrip-aXXo.en.HI.srt
Processing file: New.In.Town.2009.WEBRip.Amazon.srt
Processing file: New.Years.Eve.2011.720p.BrRip.x264.YIFY.srt
Text not found in sentences: Mom. KIM:
Processing file: New.York.Minute.2004.1080p.WEBRip.x264-RARBG.hi.eng.srt
Processing file: Next.Friday.2000.720p.BluRay.x264.YIFY-eng.srt
Processing file: ngd.bdrip.x264-no1_sdh.srt
Processing file: Night At The Museum 2009 Battle Of The Smithsonian SDH Subtitles English.srt
Skipping file: Night At The Museum 2009 Battle Of The Smithsonian SDH Subtitles English.srt as all values in the 'speaker' column are NA's.
Processing file: Night.At.The.Museum.2006.DVDRip.XviD-UnSeeN.ENG.srt
Skipping file: Night.At.The.Museum.2006.DVDRip.XviD-UnSeeN.ENG.srt as all values in the 'speaker' column are NA's.
Processing file: Night.At.The.Museum.2006.DVDRip.XviD-UnSeeN.ENG_HI.srt
Skipping file: Night.At.The.Museum.2006.DVDRip.XviD-UnSeeN.ENG_HI.srt as all values in the 'speaker' column are NA's.
Processing file: Night.at.the.Museum.Secret.of.the.Tomb.2014.BRRip.XViD.srt
Processing file: Night.School.2018.1080p.WEB-DL.H264.AC3-EVO.srt
Processing file: Nightcrawler.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Ninja.Assassin.2009.DVDRip.XviD-aXXo.Hi.srt
Processing file: No.Escape.2015.BDRip.x264-DRONES.srt
Processing file: No.Strings.Attached.2011.WEBRip.Amazon.srt
Skipping file: No.Strings.Attached.2011.WEBRip.Amazon.srt as all values in the 'speaker' column are NA's.
Processing file: Noah.2013.720p.BluRay.srt
Processing file: nobel-son-arigold.en.HI.srt
Skipping file: nobel-son-arigold.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Nobodys.Fool.2018.1080p.WEB-DL.DD5.1.srt
Skipping file: Nobodys.Fool.2018.1080p.WEB-DL.DD5.1.srt as all values in the 'speaker' column are NA's.
Processing file: Non-Stop.2014.720p.BluRay.X264-AMIABLE-HI.srt
Processing file: North.Country.2005.720p.WEB-DL.HDCLUB.HI.srt
Processing file: Notorious.UNRATED.DVDRip.srt
Skipping file: Notorious.UNRATED.DVDRip.srt as all values in the 'speaker' column are NA's.
Processing file: Now.You.See.Me.2013.EXTENDED.720p.BluRay.x264-SPARKS.srt
Processing file: Nurse Betty (2000).CC.srt
Skipping file: Nurse Betty (2000).CC.srt as all values in the 'speaker' column are NA's.
Processing file: O.DVDRip.DivX-DOMiNiON.ENG.srt
Skipping file: O.DVDRip.DivX-DOMiNiON.ENG.srt as all values in the 'speaker' column are NA's.
Processing file: Oblivion.2013.720p.BluRay.x264-SPARKS.srt
Processing file: Observe.And.Report.DVDRip.XviD-DiAMOND.Hi.srt
Processing file: Oceans.8.2018.720p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Oceans.Eleven.2001.720p.Bluray.x264.YIFY.HI.srt
Processing file: Oceans.Twelve.2004.D.BDRip1080.Engl.srt
Processing file: Oculus.2013.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Old.School.2003.srt
Skipping file: Old.School.2003.srt as all values in the 'speaker' column are NA's.
Processing file: Oldboy.2013.720p.BluRay.srt
Processing file: Olympus.Has.Fallen.2013.1080p.Blu-ray.AVC.DTS-HD.MA.srt
Skipping file: Olympus.Has.Fallen.2013.1080p.Blu-ray.AVC.DTS-HD.MA.srt as all values in the 'speaker' column are NA's.
Processing file: On The Line ENG _Hosen_.srt
Processing file: Once Upon a Time in Mexico (2003) U.S.A BD.srt
Processing file: Once.Upon.A.Time.....In.Hollywood.2019.720p.WEBRip.x264-[YTS.LT].Hi.srt
Processing file: One.Day.2011.1080p.BluRay.x264-SECTOR7.Hi.srt
Processing file: One.Direction.This.Is.Us.2013.EXTENDED.720p.BluRay.DTS.x264.PublicHD-sdh.srt
Processing file: One.for.the.Money.2012.720p.US.BluRay.x264.DTS-HDChina.english.srt
Skipping file: One.for.the.Money.2012.720p.US.BluRay.x264.DTS-HDChina.english.srt as all values in the 'speaker' column are NA's.
Processing file: One.Missed.Call.srt
Processing file: One.Night.with.the.King.2006.Hi.srt
Processing file: Open Range CD1.English.srt
Processing file: Open Range CD2.English.srt
Processing file: Operation.Finale.2018.720p.NF.WEB-DL.DD5.1.H264-CMRG-HI.srt
Skipping file: Operation.Finale.2018.720p.NF.WEB-DL.DD5.1.H264-CMRG-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Orphan.2009-DVDRip.XviD-DiAMOND.srt
Processing file: Ouija.2014.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Ouija.Origin.of.Evil.2016.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Our Family Wedding.2010.DvdRip.Xvid {1337x}-Noir.srt
Processing file: Our.Brand.Is.Crisis.2015.720p.BluRay.x264-Replica.HI.srt
Processing file: Our.Idiot.Brother.BDRip.XviD-DiAMOND.srt
Skipping file: Our.Idiot.Brother.BDRip.XviD-DiAMOND.srt as all values in the 'speaker' column are NA's.
Processing file: Out.of.the.Furnace.2013.720p.BluRay.x264-SPARKS-SDH.srt
Processing file: Out.of.Time.2003.Blu-ray.720p.DTS.x264-CHD-hi.srt
Processing file: Over Her Dead Body. [2008].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Over Her Dead Body. [2008].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Overboard.2018.720p.BluRay.x264.srt
Processing file: Overcomer.2019.720p.WEBRip.800MB.x264-GalaxyRG-HI.srt
Processing file: Overlord.2018.1080p.PROPER.WEB-DL.X264.5.1-SeeHD-HI.srt
Processing file: Oz.the.Great.and.Powerful.2013.720p.BluRay.x264-SPARKS.srt
Processing file: p-n.srt
Skipping file: p-n.srt as all values in the 'speaker' column are NA's.
Processing file: p-rod.eng_HI.srt
Processing file: P.S.I.Love.You[2007]DvDrip[Eng]-aXXo.en.HI.srt
Processing file: Pacific.Rim.2013.720p.BluRay.x264-SPARKS.srt
Processing file: Pacific.Rim.Uprising.2018.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Paddington.2.2017.WEB-DL.x264-FGT-HI.srt
Processing file: Paddington.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Pain.and.Gain.2013.720p.BluRay.X264-AMIABLE.srt
Skipping file: Pain.and.Gain.2013.720p.BluRay.X264-AMIABLE.srt as all values in the 'speaker' column are NA's.
Processing file: Pandorum[2009]DvDrip[Eng]-FXG.en.srt
Skipping file: Pandorum[2009]DvDrip[Eng]-FXG.en.srt as all values in the 'speaker' column are NA's.
Processing file: paparazzi.2004.internal.dvdrip.xvid-undead.ing.srt
Skipping file: paparazzi.2004.internal.dvdrip.xvid-undead.ing.srt as all values in the 'speaker' column are NA's.
Processing file: Paper.Towns.2015.720p.BluRay.x264-ALLiANCE-HI.srt
Processing file: Paranoia.2013.720p.BluRay.x264-SPARKS.srt
Skipping file: Paranoia.2013.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: Paranormal.Activity-The.Ghost.Dimension.2015.HD-TS.XVID.AC3.Hive-CM8.srt
Skipping file: Paranormal.Activity-The.Ghost.Dimension.2015.HD-TS.XVID.AC3.Hive-CM8.srt as all values in the 'speaker' column are NA's.
Processing file: Paranormal.Activity.3.2011.UNRATED.DVDRip.XviD-SPARKS.Hi.srt
Processing file: Paranormal.Activity.4.2012.UNRATED.720p.BluRay.x264-SPARKS.eng.srt
Processing file: Paranormal.Activity.The.Marked.Ones.2014.UNRATED.HDRip.XviD-AQOS-hi.srt
Processing file: paranormalActivity2-faye-xvid.Hi.srt
Skipping file: paranormalActivity2-faye-xvid.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Parental Guidance.[2012].DVDRIP.DIVX.srt
Skipping file: Parental Guidance.[2012].DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Parker.2013.720p.BluRay.DTS.x264-PublicHD.srt
Processing file: Passengers.2016.720p.BluRay.x264-SPARKS.HI.srt
Processing file: Pathfinder.EXTENDED.2007.1080p.BluRay.HI.x264.mkv.srt
Processing file: Paycheck 2003 720p BRRip Hearinng Impaired.srt
Skipping file: Paycheck 2003 720p BRRip Hearinng Impaired.srt as all values in the 'speaker' column are NA's.
Processing file: Pearl Harbor 2001 720p BRRip x264 vice.srt
Processing file: Peeples 2013 HDRip XviD-AQOS.srt
Processing file: Penelope.[2006].RETAIL.DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Penelope.[2006].RETAIL.DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: People.Like.Us.2012.720p.BluRay.x264-ALLiANCE.english.srt
Processing file: Peppermint.2018.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Percy Jackson & the Olympians The Lightning Thief.[2010].R5.DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Skipping file: Percy Jackson & the Olympians The Lightning Thief.[2010].R5.DVDRIP.INTEL.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Percy.Jackson.Sea.of.Monsters.2013.720p.BluRay.x264.YIFY[English].srt
Skipping file: Percy.Jackson.Sea.of.Monsters.2013.720p.BluRay.x264.YIFY[English].srt as all values in the 'speaker' column are NA's.
Processing file: Perfect.Stranger[2007]DvDrip[Eng]-aXXo.srt
Processing file: Persecuted.2014.720p.BluRay.x264-BRMP-HI.srt
Processing file: Pet.Sematary.2019.1080p.HC.HDRip.X264-EVO-HI.srt
Processing file: Peter.Pan.2003.720p.BluRay.x264-SiNNERS.eng.srt
Skipping file: Peter.Pan.2003.720p.BluRay.x264-SiNNERS.eng.srt as all values in the 'speaker' column are NA's.
Processing file: pg.dvdrip.xvid-deityINGLES.srt
Skipping file: pg.dvdrip.xvid-deityINGLES.srt as all values in the 'speaker' column are NA's.
Processing file: Phantom.2013.720p.BluRay.DTS.x264-PublicHD.srt
Skipping file: Phantom.2013.720p.BluRay.DTS.x264-PublicHD.srt as all values in the 'speaker' column are NA's.
Processing file: Phoenix.Forgotten.2017.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Phone.Booth.2002.720p.BrRip.x264.YIFY.srt
Processing file: Pineapple.Express.Unrated.2008.1080p.BluRay.x264.anoXmous_eng.srt
Processing file: Piranha 3D (2010).srt
Skipping file: Piranha 3D (2010).srt as all values in the 'speaker' column are NA's.
Processing file: Pirates of the Caribbean - Dead Mans Chest (2006).srt
Skipping file: Pirates of the Caribbean - Dead Mans Chest (2006).srt as all values in the 'speaker' column are NA's.
Processing file: Pirates.of.the.Caribbean.The.Curse.of.the.Black.Pearl.2003.DVDRip.XviD-UnSeeN.srt
Processing file: Pitch.Black.2000.BluRay.1080p.x264.srt
Processing file: Pitch.Perfect.2.2015.720p.BluRay.x264-SPARKS.srt
Processing file: Pitch.Perfect.3.2017.HC.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Pixels.2015.720p.BluRay.x264-DRONES-HI.srt
Processing file: Planet.Of.The.Apes.2001.DVDRip.XviD.DTS-UnSeeN.srt
Processing file: Playing.for.Keeps.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: Playing.with.Fire.2019.1080p.WEB-DL.DD5.1.x264-CMRG-HI.srt
Processing file: Pokemon.Detective.Pikachu.2019.720p.BluRay.x264-AAA-HI.srt
Skipping file: Pokemon.Detective.Pikachu.2019.720p.BluRay.x264-AAA-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Poltergeist 2015 Screener XViD-ETRG.srt
Processing file: Pompeii.2014.720p.BluRay.x264-BLOW-HI.srt
Processing file: Poms.2019.720p.NF.WEB-DL.DDP5.1.srt
Skipping file: Poms.2019.720p.NF.WEB-DL.DDP5.1.srt as all values in the 'speaker' column are NA's.
Processing file: Pootie.Tang.2001.1080p.WEBRip.DD5.1.x264-monkee.srt
Skipping file: Pootie.Tang.2001.1080p.WEBRip.DD5.1.x264-monkee.srt as all values in the 'speaker' column are NA's.
Processing file: Poseidon.2006.1080p.BluRay.x264.DTS-HD.MA.5.1-iND.en-EN[SDH].srt
Processing file: Power.Rangers.2017.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Predators.[2010].R5.DVDRIP.H264.[Eng]-DUQA.srt
Skipping file: Predators.[2010].R5.DVDRIP.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Premium.Rush.2012.PROPER.720p.BluRay.x264-DAA.eng.srt
Skipping file: Premium.Rush.2012.PROPER.720p.BluRay.x264-DAA.eng.srt as all values in the 'speaker' column are NA's.
Processing file: prevail.saw5.srt
Skipping file: prevail.saw5.srt as all values in the 'speaker' column are NA's.
Processing file: Pride.And.Glory[2008]DvDrip-aXXo.en.HI.srt
Processing file: Priest.2011.ENGLiSH.Closed.Caption.DVDRip-Retail.srt
Processing file: Prime.DVDRip.XviD-DiAMOND.srt
Skipping file: Prime.DVDRip.XviD-DiAMOND.srt as all values in the 'speaker' column are NA's.
Processing file: Princess Diaries - 1CD - Eng - 2001.srt
Processing file: Prisoners.2013.720p.BluRay.x264-SPARKS.srt
Skipping file: Prisoners.2013.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: Project.Almanac.2014.720p.BluRay.srt
Processing file: Project.X.2012.EXTENDED.720p.BluRay.X264-AMIABLE.english.srt
Processing file: Prom.Night.2008.WEB-DL.NF_HI.en.srt
Text not found in sentences: Detective Winn, Bridgeport PD.
 
Processing file: Prometheus.[2012].New.1280X720P.TS.DIVX.[Eng]-DUQA.srt
Processing file: Proof.Of.Life.2000.1080p.WEBRip.x264.AAC5.1-[YTS.MX].srt
Processing file: Proud.Marry.2018.NEW.HD-TS.X264-CPG-HI.srt
Processing file: Public.Enemies.2009.DvDRip-FxM.srt
Processing file: Pukka.R5.Line.p-310.srt
Skipping file: Pukka.R5.Line.p-310.srt as all values in the 'speaker' column are NA's.
Processing file: Pulse.2006.HD.DVDRip.720p.x264.AC3-5.1-iLL.srt
Processing file: Punisher-War.Zone[2008]DvDrip-aXXo.srt
Processing file: Quarantine.WEBRip.Netflix.en[cc].srt
Processing file: Queen Of The Damned_eng-SDH.srt
Processing file: Queen.and.Slim.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: R.I.P.D.2013.720p.BluRay.srt
Processing file: Race.To.Witch.Mountain.2009.BRRip.XviD.AC3-ViSiON.(Hi).srt
Skipping file: Race.To.Witch.Mountain.2009.BRRip.XviD.AC3-ViSiON.(Hi).srt as all values in the 'speaker' column are NA's.
Processing file: Racing.Stripes.2005.720p.WEB-DL.DD5.1.H264-FGT.srt
Processing file: Raise.Your.Voice.2004.1080p.WEBRip.x264-RARBG.srt
Processing file: Rambo Last Blood (2019).srt
Processing file: Rambo.2008.Eng.R5.DVDRip.DivX-LTT.srt
Skipping file: Rambo.2008.Eng.R5.DVDRip.DivX-LTT.srt as all values in the 'speaker' column are NA's.
Processing file: Ramona.and.Beezus.2010.720p.BDRip.x264.AC3-Zoo_eng.srt
Skipping file: Ramona.and.Beezus.2010.720p.BDRip.x264.AC3-Zoo_eng.srt as all values in the 'speaker' column are NA's.
Processing file: Rampage.2018.720p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Rat.Race.2001.1080p.WEBRip.x264-[YTS.AM].srt
Skipping file: Rat.Race.2001.1080p.WEBRip.x264-[YTS.AM].srt as all values in the 'speaker' column are NA's.
Processing file: Ready.or.Not.2019.DVDRip.XviD.AC3-EVO-HI.srt
Processing file: Ready.Player.One.2018.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Real Steel 2011 BluRay 3Li 1080p English (Hearing Impaired).srt
Skipping file: Real Steel 2011 BluRay 3Li 1080p English (Hearing Impaired).srt as all values in the 'speaker' column are NA's.
Processing file: Rebound (2005).srt
Skipping file: Rebound (2005).srt as all values in the 'speaker' column are NA's.
Processing file: Red (2010) eng.720p.srt
Processing file: Red Eye (2005) (UHD Blu-ray).srt
Processing file: Red.2.2013.BDRip.srt
Processing file: Red.Dawn.2012.720p.BluRay.DTS.x264-PublicHD.eng.srt
Skipping file: Red.Dawn.2012.720p.BluRay.DTS.x264-PublicHD.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Red.Dragon.2002.720p.BluRay.x264.DTS-WiKi.Hi.srt
Processing file: Red.Planet.2000.1080p.REPACK.BluRay.x264-7SinS.Hi.srt
Processing file: Red.Riding.Hood.DVDRip.XviD-DEFACED.Hi.srt
Processing file: Red.Sparrow.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: Red.Tails.2012.AC3.720p.BRRip.XViD-RemixHD-eng.srt
Processing file: reign over me cd1.srt
Processing file: reign over me cd2.srt
Skipping file: reign over me cd2.srt as all values in the 'speaker' column are NA's.
Processing file: Reindeer_Games_english.srt
Skipping file: Reindeer_Games_english.srt as all values in the 'speaker' column are NA's.
Processing file: Remember Me.srt
Processing file: Remember.The.Titans.(2000).Directors.Cut.DVDRip.AC3.XviD.CD1-FRAGMENT.srt
Skipping file: Remember.The.Titans.(2000).Directors.Cut.DVDRip.AC3.XviD.CD1-FRAGMENT.srt as all values in the 'speaker' column are NA's.
Processing file: Remember.The.Titans.(2000).Directors.Cut.DVDRip.AC3.XviD.CD2-FRAGMENT.srt
Skipping file: Remember.The.Titans.(2000).Directors.Cut.DVDRip.AC3.XviD.CD2-FRAGMENT.srt as all values in the 'speaker' column are NA's.
Processing file: Rendition.eng.srt
Processing file: Reno.911.Miami.UNRATED.DVDRip.srt
Processing file: Replicas.2018.720p.BluRay.x264-.YTS.AM.-HI.srt
Skipping file: Replicas.2018.720p.BluRay.x264-.YTS.AM.-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Resident Evil Afterlife 2010 R5.[2010].DVDRIP.DIVX.[Eng]-DUQA.srt
Skipping file: Resident Evil Afterlife 2010 R5.[2010].DVDRIP.DIVX.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Resident Evil Retribution.[2012].DVDRIP.DIVX.srt
Skipping file: Resident Evil Retribution.[2012].DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Resident Evil.2.Apocalypse.[2004].DVDRIP.H264.[Eng]-DUQA.srt
Skipping file: Resident Evil.2.Apocalypse.[2004].DVDRIP.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Resident Evil.3.Extinction.[2007].DVDRIP.H264.[Eng]-DUQA.srt
Skipping file: Resident Evil.3.Extinction.[2007].DVDRIP.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Resident.Evil.2002.720p.BluRay.x264.DTS-WiKi-SDH.srt
Skipping file: Resident.Evil.2002.720p.BluRay.x264.DTS-WiKi-SDH.srt as all values in the 'speaker' column are NA's.
Processing file: Resident.Evil.The.Final.Chapter.2016.BluRay.1080p.TrueHD.Atmos.7.1.AVC.HYBRID.REMUX-FraMeSToR.English.srt
Processing file: Resurrecting the Champ (2007) BluRay 720p.srt
Skipping file: Resurrecting the Champ (2007) BluRay 720p.srt as all values in the 'speaker' column are NA's.
Processing file: Richard.Jewell.2019.DVDSCR.srt
Skipping file: Richard.Jewell.2019.DVDSCR.srt as all values in the 'speaker' column are NA's.
Processing file: Ricki.and.the.Flash.2015.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Riddick.2013.EXTENDED.1080p.BluRay.x264-ALLiANCE-SDH.srt
Processing file: Ride.Along.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Righteous.Kill[2008]DvDrip-aXXo.en.HI.srt
Skipping file: Righteous.Kill[2008]DvDrip-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Rings.2017.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Rise of the Planet of the Apes 2011 BRRip XVID AbSurdiTy.srt
Skipping file: Rise of the Planet of the Apes 2011 BRRip XVID AbSurdiTy.srt as all values in the 'speaker' column are NA's.
Processing file: Road.to.Perdition.2002.1080p.BluRay.x264.anoXmous_eng.srt
Processing file: road_trip.srt
Skipping file: road_trip.srt as all values in the 'speaker' column are NA's.
Processing file: Robin Hood.[2010].R5.DVDRIP.H264.[Eng]-DUQA.srt
Skipping file: Robin Hood.[2010].R5.DVDRIP.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Robin.Hood.2018.HDCAM.XviD-AVID-HI.srt
Processing file: Robocop.2014.720p.BluRay.srt
Processing file: Rock.Of.Ages.2012.EXTENDED.720p.BluRay.x264.YIFY.srt
Processing file: rock.star.2001.1080p.bluray.x264.sdh.srt
Processing file: Rock.the.Kasbah.2015.720p.WEB-DL.x264.AC3-ETRG.HI.srt
Skipping file: Rock.the.Kasbah.2015.720p.WEB-DL.x264.AC3-ETRG.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Rocketman.2019.720p.BluRay.srt
Skipping file: Rocketman.2019.720p.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: Rocky Balboa 2006 1080p Blu-ray Remux AVC LPCM 5.srt
Processing file: Rogue.One.2016.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Role Models Eng.srt
Processing file: Romeo.Must.Die.2000.720p.BluRay.x264-KaKa.Hi.srt
Processing file: Rules of Engagement ENG.srt
Skipping file: Rules of Engagement ENG.srt as all values in the 'speaker' column are NA's.
Processing file: Rules.Dont.Apply.2016.720p.BluRay.x264-DRONES.HI.srt
Processing file: Run.All.Night.2015.720p.BluRay.x264-SPARKS.srt
Processing file: Run.the.Race.2019.720p.HDCAM-1XBET-HI.srt
Skipping file: Run.the.Race.2019.720p.HDCAM-1XBET-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Runner.Runner.2013.HDRip.X264-PLAYNOW-hi.srt
Processing file: Running.Scared[2006]DvDrip[Eng]-aXXo.srt
Processing file: Rush.Hour.2.2001.1080p.BluRay.X264-AMIABLE.srt
Processing file: Rush.Hour.3.2007.720p.BluRay.x264.VPPV.srt
Processing file: Sabotage.2014.1080p.WEB-DL.DD5.1.srt
Skipping file: Sabotage.2014.1080p.WEB-DL.DD5.1.srt as all values in the 'speaker' column are NA's.
Processing file: Safe.DVDRip.XviD-DoNE.Hi.srt
Skipping file: Safe.DVDRip.XviD-DoNE.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Safe.Haven.2013.720p.BluRay.x264-SPARKS.srt
Skipping file: Safe.Haven.2013.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: Safe.House.2012.DVDRiP.XviD.AC3-REFiLL.srt
Processing file: Sahara.2005.1080p.BrRip.x264.YIFY.Hi.srt
Processing file: Salt 2010 [BRRip.XviD-miguel] [ENG][HI].srt
Processing file: San.Andreas.2015.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Sanctum.2011.R5.LiNE.srt
Skipping file: Sanctum.2011.R5.LiNE.srt as all values in the 'speaker' column are NA's.
Processing file: santi-onstrangertides.brrip.xvid.srt
Skipping file: santi-onstrangertides.brrip.xvid.srt as all values in the 'speaker' column are NA's.
Processing file: Savages.2012.720p.BluRay.x264.DTS-HDChina.eng.srt
Processing file: Saving Private Ryan [1998]-keltz.srt
Skipping file: Saving Private Ryan [1998]-keltz.srt as all values in the 'speaker' column are NA's.
Processing file: saving.silverman.2001.1080p.hdtv.x264-regret.HI.eng.srt
Processing file: Saw II (Unrated Directors Cut) (108_1.srt
Text not found in sentences: It's Dad.         
Processing file: Saw.3[2006][Unrated.Edition]DvDrip-aXXo.en.HI.srt
Skipping file: Saw.3[2006][Unrated.Edition]DvDrip-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Saw.I.2004.BRRip.XviD.AC3.PRoDJi.srt
Processing file: Saw.VII.The.Final.Chapter.BDRip.XviD-Jigsaw.Hi.srt
Processing file: Scary Movie 2 (2001).en.bug-fixed.srt
Processing file: Scary Movie Pack.1.2.3.4.5.[2013].UNRATED.DVDRIP.XVID.srt
Skipping file: Scary Movie Pack.1.2.3.4.5.[2013].UNRATED.DVDRIP.XVID.srt as all values in the 'speaker' column are NA's.
Processing file: Scary.Movie.3.2003.DVDrip.ENG.srt
Processing file: Scary.Movie.5.2013.720p.BluRay.x264-GECKOS.Hi.srt
Skipping file: Scary.Movie.5.2013.720p.BluRay.x264-GECKOS.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: Scary.Stories.to.Tell.in.the.Dark.2019.1080p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: School.For.Scoundrels[2006][Unrated.Edition]DvDrip[Eng]-aXXo.srt
Processing file: Scooby Doo 2 Monsters Unleashed 2004 720p BRRip x264 AC3 DiVERSiTY.srt
Processing file: Scooby-Doo (2002).srt
Text not found in sentences: Bad Grandma!   
Processing file: Scott.Pilgrim.Vs.The.World.2010.720p.BRRip.x264-HDLiTE.Hi.srt
Processing file: Scouts Guide to the Zombie Apocalypse.2015.HDRip.XViD-ETRG.srt
Processing file: Scream.3.2000.INTERNAL.DVDRip.XviD-FiNaLe.srt
Skipping file: Scream.3.2000.INTERNAL.DVDRip.XviD-FiNaLe.srt as all values in the 'speaker' column are NA's.
Processing file: Scream.4.2011.720p.BRRip.x264.AAC-ViSiON.eng-hi.srt
Processing file: Screwed.2000.1080p.WEBRip.srt
Skipping file: Screwed.2000.1080p.WEBRip.srt as all values in the 'speaker' column are NA's.
Processing file: Seabiscuit.srt
Processing file: Season of the Witch.[2011].DVDRIP.DVX.[Eng]-DUQA.srt
Skipping file: Season of the Witch.[2011].DVDRIP.DVX.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Second.Act.2018.HDRip.XviD.AC3-EVO.srt
Skipping file: Second.Act.2018.HDRip.XviD.AC3-EVO.srt as all values in the 'speaker' column are NA's.
Processing file: Secondhand Lions (2003) 1080p BluRay.en SDH.srt
Processing file: Secret.Life.Of.Bees.2008.BRRip.XviD.AC3.D-Z0N3.ENG.srt
Skipping file: Secret.Life.Of.Bees.2008.BRRip.XviD.AC3.D-Z0N3.ENG.srt as all values in the 'speaker' column are NA's.
Processing file: Secret.Window.2004.720p.Blu.ray.DTS.srt
Processing file: Secretariat.2010.480p.BRRip.XviD.AC3-NYDIC.srt
Skipping file: Secretariat.2010.480p.BRRip.XviD.AC3-NYDIC.srt as all values in the 'speaker' column are NA's.
Processing file: See.No.Evil.2006.720p.BluRay.DTS.srt
Skipping file: See.No.Evil.2006.720p.BluRay.DTS.srt as all values in the 'speaker' column are NA's.
Processing file: SEED OF CHUCKY - Unrated [2004-Eng-DVDrip]-haSak.srt
Skipping file: SEED OF CHUCKY - Unrated [2004-Eng-DVDrip]-haSak.srt as all values in the 'speaker' column are NA's.
Processing file: Seeking.a.Friend.for.the.End.of.the.World.2012.DVDRip.XviD-SPARKS.srt
Processing file: Selfless.2015.REPACK.720p.BluRay.srt
Processing file: Serendipity.srt
Skipping file: Serendipity.srt as all values in the 'speaker' column are NA's.
Processing file: Serenity.2019.1080p.BluRay.srt
Processing file: Serenity[2005][Aka.Firefly]DvDrip[Eng]-aXXo-EN-HI.srt
Skipping file: Serenity[2005][Aka.Firefly]DvDrip[Eng]-aXXo-EN-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Serving Sara (2002) 1080p AMZN.en SDH.srt
Processing file: Seven Pounds[2008]DvDrip[Eng]-FXG.en.HI.srt
Processing file: Seven.Days.in.Utopia.2011.DVDRip.XviD-KAZAN.srt
Processing file: Seven.Psychopaths.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: Seventh.Son.2014.720p.BluRay.x264-Felony.srt
Processing file: Sex and the City[2008]DvDrip[Eng]-FXG.en.HI.srt
Processing file: Sex.And.The.City.2.DVDRip.XviD-ARROW.srt
Processing file: Sex.Drive[2008][Unrated.Edition]DvDrip-aXXo.en.HI.srt
Processing file: Sex.Tape.2014.720p.BluRay.x264-GECKOS.srt
Processing file: sha-xvid.srt
Skipping file: sha-xvid.srt as all values in the 'speaker' column are NA's.
Processing file: Shaft.2019.1080p.NF.WEB-DL.DDP5.1.srt
Skipping file: Shaft.2019.1080p.NF.WEB-DL.DDP5.1.srt as all values in the 'speaker' column are NA's.
Processing file: Shaft.srt
Skipping file: Shaft.srt as all values in the 'speaker' column are NA's.
Processing file: Shall.We.Dance.2004.1080p.BluRay.REMUX.VC-1.FLAC.5.1-TRiToN.srt
Skipping file: Shall.We.Dance.2004.1080p.BluRay.REMUX.VC-1.FLAC.5.1-TRiToN.srt as all values in the 'speaker' column are NA's.
Processing file: Shanghai Noon.srt
Skipping file: Shanghai Noon.srt as all values in the 'speaker' column are NA's.
Processing file: Shanghai.srt
Processing file: Shark.Night.BDRip.srt
Processing file: Shazam!.2019.720p.BluRay.x264-[YTS.srt
Skipping file: Shazam!.2019.720p.BluRay.x264-[YTS.srt as all values in the 'speaker' column are NA's.
Processing file: Sherlock.Holmes.2009.480p.BRRip.XviD.AC3-FLAWL3SS.en.HI.srt
Processing file: Sherlock.Holmes.A.Game.of.Shadows.2011.1080p.BluRay.x264-RSG.english.srt
Processing file: Shes Out of My League.[2010].DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Skipping file: Shes Out of My League.[2010].DVDRIP.INTEL.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Shes.the.Man.2006.1080p.WEBRip.x265-RARBG_English.srt
Processing file: Shine.2017.HDRip.AC3.x264-CMRG-HI.srt
Processing file: Shoot.Em.Up.720p.Bluray.srt
Processing file: Show.Dogs.2018.HDRip.AC33.srt
Skipping file: Show.Dogs.2018.HDRip.AC33.srt as all values in the 'speaker' column are NA's.
Processing file: showtime.srt
Skipping file: showtime.srt as all values in the 'speaker' column are NA's.
Processing file: Shutter.Island.2010.720p.BluRay.x264.DTS-WiKi.eng.srt
Processing file: Sicario.Day.of.the.Soldado.2018.720p.WEB-DL.X264.AC3-EVO-HI.srt
Processing file: Side.Effects.2013.720p.BluRay.x264.YIFY.srt
Processing file: Signs.DVDRip.XViD-ViTE ENG.srt
Processing file: Silent Hill 2006 720p BluRay DTS-ES x264-ESiR [PublicHD].srt
Processing file: Silent Hill Revelation 1080p WEB-DL DD5.1 H.264-CrazyHDSource.srt
Processing file: Silent House [2011] DVDR.srt
Skipping file: Silent House [2011] DVDR.srt as all values in the 'speaker' column are NA's.
Processing file: Sin.City.2005.Unrated.Recut.Extended.BRRip.XviD.AC3-ViSiON.srt
Skipping file: Sin.City.2005.Unrated.Recut.Extended.BRRip.XviD.AC3-ViSiON.srt as all values in the 'speaker' column are NA's.
Processing file: Sin.City.A.Dame.to.Kill.For.2014.HDRip.XviD-SaM[ETRG].srt
Skipping file: Sin.City.A.Dame.to.Kill.For.2014.HDRip.XviD-SaM[ETRG].srt as all values in the 'speaker' column are NA's.
Processing file: Sinister.2.2015.720p.BluRay.x264-BLOW.HI.srt
Skipping file: Sinister.2.2015.720p.BluRay.x264-BLOW.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Sinister.2012.720p.BluRay.X264-AMIABLE.eng.srt
Processing file: SiREN.2016.AMZN.WEBRip.DDP5.1.x264-ABM.en.srt
Skipping file: SiREN.2016.AMZN.WEBRip.DDP5.1.x264-ABM.en.srt as all values in the 'speaker' column are NA's.
Processing file: Sky.High[2005]DvDrip[Eng]-aXXo.srt
Skipping file: Sky.High[2005]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: skyfal.srt
Processing file: Skyline Corrected English Subtitles.srt
Processing file: Skyscraper.2018.1080p.BluRay.x264-SPARKS-HI.srt
Processing file: Slamma.Jamma.2017.DVDRip.XviD.srt
Processing file: Sleepless.2017.720p.BluRay.x264-GECKOS.HI.srt
Processing file: Sleepover.2004.1080p.BluRay.x264-PSYCHD.srt
Skipping file: Sleepover.2004.1080p.BluRay.x264-PSYCHD.srt as all values in the 'speaker' column are NA's.
Processing file: Sleight.2016.BDRip.x264-DRONES.srt
Processing file: Slender.Man.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: Slither.2006.BluRay.1080p.DTS.x264-CHD.ENG_HI.srt
Processing file: Smokin.Aces.2006.720p.BRRip.XviD.AC3-PsychoLogic.srt
Processing file: Snakes.On.A.Plane.2006.1080p.BluRay.x264-CiNEFiLE.ENG_HI.srt
Processing file: Snatched (2017).BluRay.x264-CECKOS.HI(Colored).srt
Processing file: Snitch.[2013].DVDRIP.DIVX.srt
Skipping file: Snitch.[2013].DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: Snow White and the Huntsman 2012 EXTENDED BDRip XviD-AMIABLE.Hi.srt
Processing file: Snow.Day.2000.1080p.WEBRip.DD5.1.x264-NTb.srt
Processing file: Snow.Dogs.2002.720p.BluRay.x264-PSYCHD-en.srt
Processing file: solaris (1972).srt
Skipping file: solaris (1972).srt as all values in the 'speaker' column are NA's.
Processing file: Solo.A.Star.Wars.Story.2018.NEW.720p.HD-TS.X264-CPG-HI.srt
Processing file: Someone_Like_You.English.srt
Processing file: Something Borrowed DVDRip XviD-TWiZTED.srt
Processing file: Son.of.God.2014.720p.BluRay.x264.YIFY-eng.srt
Skipping file: Son.of.God.2014.720p.BluRay.x264.YIFY-eng.srt as all values in the 'speaker' column are NA's.
Processing file: Sorority Boys (2002).srt
Skipping file: Sorority Boys (2002).srt as all values in the 'speaker' column are NA's.
Processing file: Sorority.Row.2009.DVDRip.XviD-ALLiANCE.srt
Skipping file: Sorority.Row.2009.DVDRip.XviD-ALLiANCE.srt as all values in the 'speaker' column are NA's.
Processing file: Soul.Surfer.2011.BRRip.720p.DTS.srt
Processing file: Southpaw.2015.720p.WEB-DL.AAC.2.0.srt
Processing file: Sparkle.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: sparks-trd2011-720.hearing impaired.srt
Processing file: Speed.Racer[2008]DvDrip-aXXo.en.HI.srt
Processing file: Spider-Man(2004)2-720p.BluRay.x264.AC3.srt
Processing file: Spider-Man.Far.from.Home.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Spiderman - english.srt
Skipping file: Spiderman - english.srt as all values in the 'speaker' column are NA's.
Processing file: Spiderman.3.TS.XViD-mVs.CD1.en.srt
Skipping file: Spiderman.3.TS.XViD-mVs.CD1.en.srt as all values in the 'speaker' column are NA's.
Processing file: Spiderman.3.TS.XViD-mVs.CD2.en.srt
Processing file: Splice (2009).srt
Processing file: Split.2016.720p.BluRay.srt
Processing file: Spy Game.srt
Skipping file: Spy Game.srt as all values in the 'speaker' column are NA's.
Processing file: Spy Kids 2 DVDRip Occor.srt
Skipping file: Spy Kids 2 DVDRip Occor.srt as all values in the 'speaker' column are NA's.
Processing file: Spy Kids.srt
Processing file: Spy.2015.720p.BluRay.srt
Processing file: Spy.Kids.3.Game.Over.2003.1080p.BluRay.x264.DTS-FGT.srt
Skipping file: Spy.Kids.3.Game.Over.2003.1080p.BluRay.x264.DTS-FGT.srt as all values in the 'speaker' column are NA's.
Processing file: Stand.Up.Guys.2012.720p.BluRay.x264-DAA.srt
Skipping file: Stand.Up.Guys.2012.720p.BluRay.x264-DAA.srt as all values in the 'speaker' column are NA's.
Processing file: Star Trek Nemesis (2002)_[eng](deaf).srt
Processing file: Star.Trek.2009.720p.BRRip.XviD.AC3-ViSiON.srt
Processing file: Star.Trek.Into.Darkness.2013.BluRay.720p.x264-HDWinG.srt
Skipping file: Star.Trek.Into.Darkness.2013.BluRay.720p.x264-HDWinG.srt as all values in the 'speaker' column are NA's.
Processing file: Star.Wars.Episode.1.The.Phantom.Menace.1999.BluRay.720p.DTS-ES.2Audio.x264-CHD.Eng.srt
Skipping file: Star.Wars.Episode.1.The.Phantom.Menace.1999.BluRay.720p.DTS-ES.2Audio.x264-CHD.Eng.srt as all values in the 'speaker' column are NA's.
Processing file: Star.Wars.Episode.III.Revenge.of.the.Sith.SDH.Bluray.New.By.Ryan.srt
Processing file: Star.Wars.Episode.IX.The.Rise.of.Skywalker.2020.BDRip.XviD.AC3-EVO-HI.srt
Processing file: Star.Wars.The.Last.Jedi.2017.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Stardust[2007]DvDrip[Eng]-FXG.srt
Skipping file: Stardust[2007]DvDrip[Eng]-FXG.srt as all values in the 'speaker' column are NA's.
Processing file: Stay[2005]DvDrip.AC3[Eng]-aXXo.srt
Skipping file: Stay[2005]DvDrip.AC3[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: Stealth.2005.DVDRip.XviD.DTS.iNT.CD1-MiNY.ShareHeaven.srt
Skipping file: Stealth.2005.DVDRip.XviD.DTS.iNT.CD1-MiNY.ShareHeaven.srt as all values in the 'speaker' column are NA's.
Processing file: Stealth.2005.DVDRip.XviD.DTS.iNT.CD2-MiNY.ShareHeaven.srt
Skipping file: Stealth.2005.DVDRip.XviD.DTS.iNT.CD2-MiNY.ShareHeaven.srt as all values in the 'speaker' column are NA's.
Processing file: Stealth.2005.DVDRip.XviD.DTS.iNT.CD3-MiNY.ShareHeaven.srt
Skipping file: Stealth.2005.DVDRip.XviD.DTS.iNT.CD3-MiNY.ShareHeaven.srt as all values in the 'speaker' column are NA's.
Processing file: Step Up 3 (2010).720X576.srt
Processing file: Step.Brothers.2008.Unrated.2160p.UHD.BluRay.REMUX.HDR.HEVC.Atmos-EPSiLON_en.sdh.srt
Processing file: Step.Up.2-The.Streets[2008]DvDrip-aXXo.en.HI.srt
Skipping file: Step.Up.2-The.Streets[2008]DvDrip-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Step.Up.All.In.2014.720p.WEB-DL.DD5.1.H264-RARBG.srt
Skipping file: Step.Up.All.In.2014.720p.WEB-DL.DD5.1.H264-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: Step.Up.Revolution.2012.720p.Bluray.x264-Replica.srt
Processing file: stepup1.srt
Skipping file: stepup1.srt as all values in the 'speaker' column are NA's.
Processing file: stepup2.srt
Skipping file: stepup2.srt as all values in the 'speaker' column are NA's.
Processing file: Stop-Loss[2008]DvDrip-aXXo.en.HI.srt
Processing file: Straight.Outta.Compton.2015.DC.720p.BluRay.x264-VETO.HI.srt
Processing file: Stranger.Than.Fiction.2006.1080p.BluRay.DD5.1.x264-EbP_en.sdh.srt
Processing file: Straw.Dogs.2011.DVDRip.XviD-ViP3R.Hi.srt
Processing file: Street.Kings[2008]DvDrip-aXXo.en.HI.srt
Processing file: Stuber.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Stuck On You - English Hearing Impaired (29_970 FPS).srt
Skipping file: Stuck On You - English Hearing Impaired (29_970 FPS).srt as all values in the 'speaker' column are NA's.
Processing file: Sucker.Punch.2011.DVDRip.XviD-MAXSPEED.Hi.srt
Processing file: Sugar . Spice (2001) 1080p AMZN.en SDH.srt
Skipping file: Sugar . Spice (2001) 1080p AMZN.en SDH.srt as all values in the 'speaker' column are NA's.
Processing file: Super Troopers (Hearing Impaired).srt
Skipping file: Super Troopers (Hearing Impaired).srt as all values in the 'speaker' column are NA's.
Processing file: Super.8.2011.BluRay.1080p.x264.DTS-HDChina.eng.srt
Processing file: Super.Troopers.2.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: Superbad[2007][Unrated Editon]DvDrip[Eng]-D_Mania.srt
Skipping file: Superbad[2007][Unrated Editon]DvDrip[Eng]-D_Mania.srt as all values in the 'speaker' column are NA's.
Processing file: SuperFly.2018.720p.BluRay.x264-Replica-HI.srt
Processing file: Superhero.Movie[2008]DvDrip.AC3-aXXo.en.HI.srt
Skipping file: Superhero.Movie[2008]DvDrip.AC3-aXXo.en.HI.srt as all values in the 'speaker' column are NA's.
Processing file: Superman Returns.srt
Skipping file: Superman Returns.srt as all values in the 'speaker' column are NA's.
Processing file: Surrogates.[2009].RETAIL.DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Surrogates.[2009].RETAIL.DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Surviving.Christmas.DVDRiP.XViD-DEiTY.hearing.impaired.srt
Skipping file: Surviving.Christmas.DVDRiP.XViD-DEiTY.hearing.impaired.srt as all values in the 'speaker' column are NA's.
Processing file: Suspect Zero 2004 720p WEB-DL.eng.hi.srt
Processing file: Sweeney.Todd.2007.720p.BluRay.srt
Processing file: Sweet.November.2001.1080p.WEBRip.x264-RARBG.English.SDH.srt
Processing file: Swimfan (2002 Web Rip)_HI.srt
Skipping file: Swimfan (2002 Web Rip)_HI.srt as all values in the 'speaker' column are NA's.
Processing file: Swing.Vote.2008.WEBRip.Amazon.srt
Skipping file: Swing.Vote.2008.WEBRip.Amazon.srt as all values in the 'speaker' column are NA's.
Processing file: Table.19.2017.720p.BluRay.x264-DRONES.HI.srt
Processing file: Tag.2018.720p.BluRay.x264-.YTS.AM. (CHI).srt
Skipping file: Tag.2018.720p.BluRay.x264-.YTS.AM. (CHI).srt as all values in the 'speaker' column are NA's.
Processing file: Take.Me.Home.Tonight.BDRip.XviD-TARGET.Hi.srt
Processing file: Taken.2.2012.UNRATED.EXTENDED.720p.BluRay.x264-DAA.eng.srt
Skipping file: Taken.2.2012.UNRATED.EXTENDED.720p.BluRay.x264-DAA.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Taken.2008.BluRay.1080p.DTS.x264.dxva-EuReKA.ENG_HI.srt
Processing file: Taken.3.2014.EXTENDED.720p.BluRay.x264-SPARKS.srt
Processing file: Taking Lives 2004 Unrated DC 720p Bluray AC3 x264-EbP.srt
Processing file: Taking.Woodstock.720p.Bluray.x264-CBGB.eng.srt
Processing file: Tammy.2014.EXTENDED.720p.BluRay.x264-GECKOS-HI.srt
Processing file: Tears.Of.The.Sun.2003.720p.BrRip.x264.YIFY.srt
Processing file: tec.dvdrip.xvid-deity.english.srt
Skipping file: tec.dvdrip.xvid-deity.english.srt as all values in the 'speaker' column are NA's.
Processing file: Ted.2.2015.720p.BluRay.srt
Processing file: Ted.2012.720p.BluRay.x264.DTS-HDChina.eng.srt
Skipping file: Ted.2012.720p.BluRay.x264.DTS-HDChina.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Teenage.Mutant.Ninja.Turtles.2014.720p.BluRay.x264-SPARKS.srt
Processing file: Terminator Salvation.[2009].R5.DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Terminator Salvation.[2009].R5.DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Terminator.3.Rise.Of.The.Machines.2003.1920x790.BDRip.x264.TrueHD.srt
Processing file: Terminator.Dark.Fate.2019.1080p.WEB-DL.DD5.1.x264-CMRG-HI.srt
Processing file: Terminator.Genisys.2015.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Texas.Chainsaw.2013.720p.BluRay.DTS.x264-HDWinG.srt
Skipping file: Texas.Chainsaw.2013.720p.BluRay.DTS.x264-HDWinG.srt as all values in the 'speaker' column are NA's.
Processing file: That.Awkward.Moment.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: thats.my.boy.2012.720p.bluray.x264-sparks.eng-hi.srt
Processing file: The 40 Year Old Virgin (2005)-Unrated-Eng-WS-Divx-AC3-BuRnT-.srt
Skipping file: The 40 Year Old Virgin (2005)-Unrated-Eng-WS-Divx-AC3-BuRnT-.srt as all values in the 'speaker' column are NA's.
Processing file: The A Team 2010.srt
Skipping file: The A Team 2010.srt as all values in the 'speaker' column are NA's.
Processing file: The Avengers 2012 3Li BluRay 720p English (Hearing Impaired).srt
Processing file: The Beach (2000).BRRip.1080p.Dual.[Hindi-Eng].AAC.srt
Processing file: The Big Lebowski.srt
Processing file: The Book of Eli.[2010].DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Skipping file: The Book of Eli.[2010].DVDRIP.INTEL.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: The Bourne Identity[2002]DvDrip AC3[Eng]-FXG.srt
Processing file: The Cabin in the Woods.[2011].R6.LINE.DVDRIP.DIVX.srt
Skipping file: The Cabin in the Woods.[2011].R6.LINE.DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: The Cat In The Hat.srt
Skipping file: The Cat In The Hat.srt as all values in the 'speaker' column are NA's.
Processing file: The Chronicles of Narnia The Lion_ the Witch and the Wardrobe - English SDH (29_970FPS).srt
Skipping file: The Chronicles of Narnia The Lion_ the Witch and the Wardrobe - English SDH (29_970FPS).srt as all values in the 'speaker' column are NA's.
Processing file: The Chronicles of Narnia The Voyage of the Dawn Treader (2010).srt
Processing file: The Collection.srt
Processing file: The Counselor 2013 UNRATED EXTENDED.srt
Processing file: The Count of Monte Cristo - English SDH (29_970FPS).srt
Skipping file: The Count of Monte Cristo - English SDH (29_970FPS).srt as all values in the 'speaker' column are NA's.
Processing file: The Covenant 2006 720p BluRay DD5.1 x264-LoRD.srt
Processing file: The Crazies.[2010].R5.DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Skipping file: The Crazies.[2010].R5.DVDRIP.INTEL.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: The Curious Case of Benjamin Button-DVDSCR.x264.sCuM.srt
Skipping file: The Curious Case of Benjamin Button-DVDSCR.x264.sCuM.srt as all values in the 'speaker' column are NA's.
Processing file: The Curse of the Jade Scorpion.srt
Skipping file: The Curse of the Jade Scorpion.srt as all values in the 'speaker' column are NA's.
Processing file: The Dark Knight 2008 IMAX 3Li BluRay 720p English (Hearing Impaired).srt
Processing file: The Dark Knight[Eng][Subs].srt
Processing file: The Departed (2006) 1080p BluRay.en SDH.srt
Processing file: The Dilemma (2011).Hi.En.Larceny1.srt
Processing file: The Dilemma (2011).Hi.En.Larceny2.srt
Processing file: The Expendables.[2010].R5.DVDRIP.H264.[Eng]-DUQA.srt
Skipping file: The Expendables.[2010].R5.DVDRIP.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: The Eye 2008 PAL-R2UK.srt
Skipping file: The Eye 2008 PAL-R2UK.srt as all values in the 'speaker' column are NA's.
Processing file: the family man.srt
Processing file: The Fast and the Furious 2001 Blu-ray CEE 1080p VC-1 DTS 5.1.srt
Processing file: The Five Year Engagement.2012.Unrated.DVDRip.XviD.AbSurdiTy.srt
Text not found in sentences: Yeah, that's Top Chef.   
Processing file: The Founder 2016 HDRip XviD AC3-EVO.srt
Skipping file: The Founder 2016 HDRip XviD AC3-EVO.srt as all values in the 'speaker' column are NA's.
Processing file: The good shepherd.1of2.en-HI.srt
Processing file: The good shepherd.2of2.en-HI.srt
Processing file: The Great Debaters[Eng][Subs].srt
Skipping file: The Great Debaters[Eng][Subs].srt as all values in the 'speaker' column are NA's.
Processing file: The Great Raid 2005 720p BRRIP H.264 AC3 5.1-Gondy10.srt
Skipping file: The Great Raid 2005 720p BRRIP H.264 AC3 5.1-Gondy10.srt as all values in the 'speaker' column are NA's.
Processing file: The Green Hornet[Eng][Subs]-EN-HI.srt
Processing file: The Green Mile 1999 720p BluRay x264-ENG-M@.srt
Processing file: The Hangover 2 (2011) DVDRip XviD-MAXSPEED-EN-HI.srt
Skipping file: The Hangover 2 (2011) DVDRip XviD-MAXSPEED-EN-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The Hitchhikers Guide to the Galaxy[2005]DVDRip[Eng]-NuMy.srt
Skipping file: The Hitchhikers Guide to the Galaxy[2005]DVDRip[Eng]-NuMy.srt as all values in the 'speaker' column are NA's.
Processing file: The Hobbit An Unexpected Journey.[2012].RETAIL.DVDRIP.DIVX.srt
Processing file: The Hunger Games 2012 All BluRay.HI.srt
Processing file: The Hunted[888TTX]-en-2003.srt
Processing file: The In Crowd (2000).en.srt
Processing file: The Incredible Burt Wonderstone 2013 English Worldwide7477.srt
Processing file: The Incredible Hulk[2008]DvDrip[Eng]-FXG.en.HI.srt
Processing file: THE INFORMANT! [2009] DVD Rip Xvid [StB].srt
Processing file: The Internship.[2013].UNRATED.DVDRIP.DIVX.srt
Skipping file: The Internship.[2013].UNRATED.DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: The Interpreter.srt
Skipping file: The Interpreter.srt as all values in the 'speaker' column are NA's.
Processing file: The Karate Kid.[2010].DVDRIP.H264.[Eng]-DUQA.srt
Skipping file: The Karate Kid.[2010].DVDRIP.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: The Last Airbender.[2010].DVDRIP.DIVX.[Eng]-DUQA.srt
Skipping file: The Last Airbender.[2010].DVDRIP.DIVX.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: The Last Exorcism (2010).srt
Skipping file: The Last Exorcism (2010).srt as all values in the 'speaker' column are NA's.
Processing file: The Last Stand.[2013].HD.R5.LINE.DVDRIP.DIVX.srt
Skipping file: The Last Stand.[2013].HD.R5.LINE.DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: The Little Vampire 2000 BluRay 720p MkvCage.srt
Skipping file: The Little Vampire 2000 BluRay 720p MkvCage.srt as all values in the 'speaker' column are NA's.
Processing file: The Lord of the Rings - The Return of the King (2003) 23.976 fps - 263.16 min-Time Corrected-Hi.srt
Skipping file: The Lord of the Rings - The Return of the King (2003) 23.976 fps - 263.16 min-Time Corrected-Hi.srt as all values in the 'speaker' column are NA's.
Processing file: The Losers[2010]DvDrip[Eng]-FXG-EN-HI.srt
Processing file: The Majestic DVDRip DivX-English.srt
Skipping file: The Majestic DVDRip DivX-English.srt as all values in the 'speaker' column are NA's.
Processing file: The Manchurian Candidate (2004) 23.976 fps- 129.55 min version-Colored-Hi.srt
Skipping file: The Manchurian Candidate (2004) 23.976 fps- 129.55 min version-Colored-Hi.srt as all values in the 'speaker' column are NA's.
Processing file: The Medallion 2003 BluRay 1080p DTS-HD MA 2.0 AVC.srt
Processing file: The Mothman Prophecies (2002).DVDRip.HI.cc.en.CLTRSTR.srt
Processing file: The Notebook (2004) (1080p x265 10bit Tigole).srt
Processing file: The Other Boleyn Girl 2008 1080p EUR Blu-ray AVC DTS-HD MA 5.1.srt
Processing file: The Passion Of The Christ (2004).srt
Processing file: The Phantom of the Opera 2004.srt
Skipping file: The Phantom of the Opera 2004.srt as all values in the 'speaker' column are NA's.
Processing file: The Pink Panther (2006).srt
Skipping file: The Pink Panther (2006).srt as all values in the 'speaker' column are NA's.
Processing file: The Possession.[2012].DVDRIP.DIVX.srt
Skipping file: The Possession.[2012].DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: The Prestige.srt
Skipping file: The Prestige.srt as all values in the 'speaker' column are NA's.
Processing file: The Proposal.[2009].DVDRIP.DIVX.srt
Skipping file: The Proposal.[2009].DVDRIP.DIVX.srt as all values in the 'speaker' column are NA's.
Processing file: The Real Cancun (2003).DVDRip.srt
Skipping file: The Real Cancun (2003).DVDRip.srt as all values in the 'speaker' column are NA's.
Processing file: The Replacements 2000 1080p BDRemux DTS-HDMA 5.1.HI.srt
Processing file: the ring.srt
Processing file: The Rookie.srt
Skipping file: The Rookie.srt as all values in the 'speaker' column are NA's.
Processing file: The Rundown (2003).srt
Processing file: The Santa Clause 2 (2002) 720p BluRay.en SDH.srt
Processing file: The Score (2001) (1080p BluRay x265 HEVC 10bit AAC 5.1 afm72) SDH.srt
Processing file: The Scorpion King 2002.720p.BrRip.x264.YIFY.srt
Processing file: The Sin Eater [2003] XviD.srt
Processing file: The Soloist 2009 BluRay.DD5.1.x264-CtrlHD.HI.srt
Processing file: The Spy Next Door.[2010].R1.DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: The Spy Next Door.[2010].R1.DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: The Stepfather.[2009].[Unrated. Edition].DVDRIP.XVID.[Eng]-DUQA.srt
Processing file: The Talented Mr. Ripley.srt
Skipping file: The Talented Mr. Ripley.srt as all values in the 'speaker' column are NA's.
Processing file: The Texas Chainsaw Massacre The Beginning_[2006].[Unrated. Edition].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: The Texas Chainsaw Massacre The Beginning_[2006].[Unrated. Edition].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: The Thing (2011).utf8.en.srt
Processing file: The Transporter 3 (2008) BluRay.x264.srt
Processing file: The Transporter[2002]DvDrip[Eng]-NikonXp.srt
Skipping file: The Transporter[2002]DvDrip[Eng]-NikonXp.srt as all values in the 'speaker' column are NA's.
Processing file: The Tuxedo 2002 720p [Jackie Chan]-eng.srt
Processing file: The Twilight Saga Eclipse (2010).srt
Processing file: The virginity hit.en-HI.srt
Processing file: The Watch 2012 DVDrip XviD AC3-DQ1.srt
Processing file: The Words (2012) BluRay Bdrip Brrip x264 1080p 720p 480p.srt
Text not found in sentences: No, but, Dad, it doesn't work like that.
 
Processing file: the-drop.720p.BluRay.x264.YIFY.srt
Processing file: The.15.17.to.Paris.2018.720p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: The.6th.Day.2000.1080p.BluRay.AC3.x264-CtrlHD_SDH.srt
Processing file: The.Accountant.2016.720p.BluRay.x264-SPARKS.HI.srt
Processing file: The.Adjustment.Bureau.2011.720p.BluRay.DTS.x264-HDxT.srt
Processing file: The.Adventures.of.Pluto.Nash.2002.1080p.WEBRip.x264-RARBG.srt
Processing file: The.Adventures.Of.Sharkboy.And.Lavagirl.In.3-D.DVDRip.XviD-DiAMOND.en.srt
Skipping file: The.Adventures.Of.Sharkboy.And.Lavagirl.In.3-D.DVDRip.XviD-DiAMOND.en.srt as all values in the 'speaker' column are NA's.
Processing file: The.Age.of.Adaline.2015.FRE.Bluray.1080p.TrueHD-7.1.Atmos.x264-Grym.SDH.srt
Processing file: the.alamo.2004.1080p.hdtv.x264-regret.sdh.eng.srt
Processing file: The.Amazing.Spider-Man.2.2014.720p.BluRay.x264-BLOW-HI.srt
Processing file: The.Amazing.Spider-Man.2012.720p.BluRay.x264.DTS-HDChina.srt
Skipping file: The.Amazing.Spider-Man.2012.720p.BluRay.x264.DTS-HDChina.srt as all values in the 'speaker' column are NA's.
Processing file: The.Animal(2001)m720p.WebRiP.x264.EAC3.srt
Skipping file: The.Animal(2001)m720p.WebRiP.x264.EAC3.srt as all values in the 'speaker' column are NA's.
Processing file: The.Apparition.2012.720p.BRRiP.XViD.AC3-LEGi0N.srt
Processing file: The.Art.of.Racing.in.the.Rain.2019.720p.HDCAM-ORCA88-HI.srt
Processing file: the.back-up.plan.2010.dvdrip.xvid-arrow.sdh.srt
Processing file: The.Banger.Sisters.DVDrip.DivX-PosTX.[english].srt
Skipping file: The.Banger.Sisters.DVDrip.DivX-PosTX.[english].srt as all values in the 'speaker' column are NA's.
Processing file: The.Bank.Job.2008.BluRay.srt
Skipping file: The.Bank.Job.2008.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: The.Beach.Bum.2019.720p.BluRay.x264-DRONES-HI.srt
Processing file: The.Benchwarmers.2006.720p.BluRay.DTS.x264-CtrlHD-SDH.srt
Processing file: The.Best.Man.Holiday.2013.720p.BluRay.x264-SPARKS-sdh.srt
Processing file: The.Best.of.Enemies.2019.HDRip.XviD.AC3-EVO-HI.srt
Skipping file: The.Best.of.Enemies.2019.HDRip.XviD.AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Best.Of.Me.2014.720p.BluRay.x264-GECKOS.srt
Processing file: The.Big.Wedding.2013.720p.BluRay.DTS.x264-PHD.srt
Processing file: The.Big.Year.2011.EXTENDED.720p.BluRay.X264-AMIABLE.English.srt
Processing file: The.Birth.of.a.Nation.2016.720p.BluRay.x264-DRONES-HI.srt
Processing file: The.Black.Dahlia[2006]DvDrip[Eng]-aXXo.srt
Processing file: The.Blind.Side.2009.1080p.BluRay.x264.YIFY.srt
Processing file: The.Book.Of.Henry.2017.720p.BluRay.x264-GECKOS.HI.srt
Processing file: The.Bounty.Hunter.DVDRip.srt
Processing file: The.Bourne.Legacy.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: The.Bourne.Ultimatum[2007]DvDrip[Eng]-aXXo.srt
Processing file: The.Box.2009.DvDRip-FxM.HI.srt
Processing file: The.Boy.Next.Door.2015.1080p.BluRay.x264-SPARKS.srt
Processing file: The.Break-Up.2006.1080p.BluRay.x264.DTS-FGT.HI.eng.srt
Processing file: The.Brothers.2001.WEBRip.x264-RARBG-sync.srt
Processing file: The.Brothers.Grimm.2005.720p.Bluray.x264-PPQ.srt
Skipping file: The.Brothers.Grimm.2005.720p.Bluray.x264-PPQ.srt as all values in the 'speaker' column are NA's.
Processing file: The.Brothers.Solomon.2007.1080p.WEB-DL.DD5.1.H264-FGT.srt
Processing file: The.Butler.2013.1080p.BluRay.x264-SPARKS-sdh1.srt
Processing file: The.Butterfly.Effect.2004.720p.AC3.5.1.x264-RMZ.en.srt
Skipping file: The.Butterfly.Effect.2004.720p.AC3.5.1.x264-RMZ.en.srt as all values in the 'speaker' column are NA's.
Processing file: The.Bye.Bye.Man.2016.UNRATED.720p.BluRay.x264-GECKOS-HI.srt
Processing file: The.Call.2012.720p.BluRay.x264-SPARKS..srt
Processing file: The.Campaign.2012.Extended.720p.BluRay.x264.DTS-HDChina.eng.srt
Processing file: The.Case.for.Christ.2017.720p.BluRay.H264.AAC-RARBG.srt
Processing file: The.Cave.DVDRip.XviD-DMT.srt
Processing file: The.Cell.2000.DC.1080p.Bluray.x264.AAC.DPLii.AlaToM_eng_sdh.srt
Processing file: The.Change-Up.UNRATED.2011.Hi.srt
Processing file: The.Chronicles.of.Riddick.BluRay.1080p.x264.5.1.Judas.srt
Processing file: The.Circle.2017.720p.BluRay.x264.DTS-HDC-HI.srt
Processing file: The.Cold.Light.Of.Day.2012.720p.BluRay.x264-HAiDEAF.(ENG)-HI.srt
Processing file: The.Conjuring.2013.720p.BluRay.x264-ALLiANCE.srt
Processing file: the.conspirator.2010.dvdrip.xvid-amiable.sdh.srt
Processing file: The.Contender.2000.DVDRip.XviD.AC3.Subs.EN-C00LdUdE.srt
Skipping file: The.Contender.2000.DVDRip.XviD.AC3.Subs.EN-C00LdUdE.srt as all values in the 'speaker' column are NA's.
Processing file: The.Cookout.2004.1080p.WEBRip.x264.AAC5.1-[YTS.MX].srt
Skipping file: The.Cookout.2004.1080p.WEBRip.x264.AAC5.1-[YTS.MX].srt as all values in the 'speaker' column are NA's.
Processing file: The.Core.2003.1080p.BluRay.x264-MOOVEE.English.srt
Skipping file: The.Core.2003.1080p.BluRay.x264-MOOVEE.English.srt as all values in the 'speaker' column are NA's.
Processing file: The.Country.Bears.2002.1080p.WEBRip.x264-RARBG.srt
Processing file: The.Crocodile.Hunter.Collision.Course.2002.1080p.AMZN.WEB-DL.DDP5.1.H.264-iJP.srt
Processing file: The.Current.War.2017.1080p.BluRay.X264-AMIABLE-HI.srt
Skipping file: The.Current.War.2017.1080p.BluRay.X264-AMIABLE-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Curse.of.La.Llorona.2019.720p.HC.HDRip.800MB.x264-GalaxyRG-HI.srt
Skipping file: The.Curse.of.La.Llorona.2019.720p.HC.HDRip.800MB.x264-GalaxyRG-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Da.Vinci.Code.2006.Extended.Cut.1080p.BluRay.H264.AAC-RARBG-English.srt
Processing file: The.Dark.Knight.Rises.2012.720p.BluRay.x264-SPARKS.eng.srt
Processing file: The.Darkest.Hour.2011.720p.BRRiP.XViD.AC3-LEGi0N_Subtitle - English.srt
Processing file: The.Darkest.Minds.2018.720p.WEB-DL.H264.AC3-EVO.srt
Processing file: The.Day.After.Tomarrow.2004.1080p.BrRip.x264.YIFY sdh.srt
Processing file: The.Day.The.Earth.Stood.Still[2008]DvDrip-aXXo.en.HI.srt
Processing file: The.Debt.2011.720p.BluRay.x264-Felony.srt
Processing file: The.Devil.Inside.2012.1080p.BluRay.X264-AMIABLE [PublicHD].srt
Processing file: The.Devil.Wears.Prada.DVDRip.XviD-DoNE.1.English.srt
Skipping file: The.Devil.Wears.Prada.DVDRip.XviD-DoNE.1.English.srt as all values in the 'speaker' column are NA's.
Processing file: The.Devil.Wears.Prada.DVDRip.XviD-DoNE.2.English.srt
Skipping file: The.Devil.Wears.Prada.DVDRip.XviD-DoNE.2.English.srt as all values in the 'speaker' column are NA's.
Processing file: The.Dictator.2012.720p.BluRay.X264-AMIABLE.srt
Processing file: The.Duff.2015.720p.BluRay.x264-ALLiANCE.srt
Processing file: The.Dukes.Of.Hazzard.2005.Unrated.Repack.1080p.HD-DVD.Remux.VC-1.DD.5.1-KRaLiMaRKo.English.srt
Processing file: The.Eagle.2011.UNRATED.720p.BRRip.XViD.AC3-FLAWL3SS - English.srt
Processing file: The.Edge.of.Seventeen.2016.720p.BluRay.x264-DRONES-HI.srt
Processing file: The.Equalizer.2.2018.1080p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: The.Equalizer.2014.720p.BluRay.x264-SPARKS.srt
Processing file: The.Expendables.2.2012.720p.BluRay.x264.DTS-HDChina.eng.srt
Processing file: The.Expendables.3.2014.EXTENDED.720p.BluRay.x264-ALLiANCE.srt
Processing file: The.Express[2008]DvDrip-aXXo.en.HI.srt
Processing file: The.Family.2013.720p.BluRay.x264.YIFY.srt
Processing file: The.Family.Stone.2005.1080p.WEBRip.x264-RARBG_English.srt
Skipping file: The.Family.Stone.2005.1080p.WEBRip.x264-RARBG_English.srt as all values in the 'speaker' column are NA's.
Processing file: The.Fast.And.The.Furious-Tokyo.Drift[2006]DvDrip[Eng]-aXXo.srt
Processing file: The.Fate.of.the.Furious.2017.720p.BluRay.x264-SPARKS.HI.srt
Processing file: The.Fault.in.Our.Stars.2014.720p.BluRay.x264-SPARKS.srt
Processing file: The.Fifth.Estate.2013.720p.BluRay.x264-SPARKS.srt
Processing file: The.Final.Destination.BDRip.XviD-iMBT-Hi.srt
Processing file: The.First.Purge.2018.720p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: the.flintstones.in.viva.rock.vegas.2000.720p.bluray.x264-spooks.srt
Processing file: The.Forbidden.Kingdom[2008]DvDrip-aXXo.en.HI.srt
Processing file: The.Fountain.2006.720p.BluRay.x264.VPPV.srt
Skipping file: The.Fountain.2006.720p.BluRay.x264.VPPV.srt as all values in the 'speaker' column are NA's.
Processing file: The.Gallows.2015.WEBRip.x264-RARBG SDH.srt
Skipping file: The.Gallows.2015.WEBRip.x264-RARBG SDH.srt as all values in the 'speaker' column are NA's.
Processing file: The.Gambler.2014.720p.BDRip.LATiNO.ENG.x264.AC3.DTS.English.SDH.srt
Text not found in sentences: In The Stranger... ...
Processing file: The.Game.Plan.2007.WEB-DL.DSNP.srt
Processing file: The.Gentlemen.2020.HDRip.XviD.AC3-EVO-HI.srt
Skipping file: The.Gentlemen.2020.HDRip.XviD.AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Gift.2015.720p.BluRay.x264-DRONES.HI.srt
Processing file: The.Girl.in.the.Spiders.Web.2018.HDRip.AC3.X264-CMRG-HI.srt
Processing file: The.Girl.Next.Door.UNRATED.2004.1080p.BrRip.x264.srt
Skipping file: The.Girl.Next.Door.UNRATED.2004.1080p.BrRip.x264.srt as all values in the 'speaker' column are NA's.
Processing file: The.Girl.On.The.Train.2016.BDRip.x264-SPARKS.en.HI.srt
Processing file: the.girl.with.the.dragon.tattoo.2011.720p.bluray.x264-sparks.english.srt
Processing file: The.Giver.2014.720p.BluRay.x264-SPARKS-HI.srt
Skipping file: The.Giver.2014.720p.BluRay.x264-SPARKS-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Glass.House.2001.1080p.WEBRip.DD5.1.x264-KiNGS.HI.eng.srt
Processing file: The.Goldfinch.2019.1080p.WEB-DL.DD5.1.srt
Skipping file: The.Goldfinch.2019.1080p.WEB-DL.DD5.1.srt as all values in the 'speaker' column are NA's.
Processing file: The.Good.Liar.2019.HDRip.XviD.AC3-EVO-HI.srt
Skipping file: The.Good.Liar.2019.HDRip.XviD.AC3-EVO-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Goods.Live.Hard.Sell.Hard.2009.1080p.WEBRip.x264-RARBG.srt
Text not found in sentences: Yeah, I told them that already, Dad.
 
Processing file: The.Great.Gatsby.2013.720p.BluRay.x264.DTS-HDWinG.srt
Skipping file: The.Great.Gatsby.2013.720p.BluRay.x264.DTS-HDWinG.srt as all values in the 'speaker' column are NA's.
Processing file: The.Great.Wall.2016.720p.BluRay.x264-GECKOS-HI.srt
Processing file: The.Greatest.Game.Ever.Played.2005.720p.BluRay.x264.AAC-ETRG.srt
Processing file: The.Greatest.Showman.2017.BluRay-CHI.srt
Skipping file: The.Greatest.Showman.2017.BluRay-CHI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Green.Inferno.2013.720p.BluRay.x264-SAPHiRE.HI.srt
Processing file: The.Grey.2011.720p.BluRay.x264.x264.YIFY.srt
Skipping file: The.Grey.2011.720p.BluRay.x264.x264.YIFY.srt as all values in the 'speaker' column are NA's.
Processing file: The.Guilt.Trip.2012.720p.BluRay.x264-SPARKS.srt
Skipping file: The.Guilt.Trip.2012.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: The.Gunman.2015.720p.WEB-DL.DD5.1.H264-RARBG.srt
Processing file: The.Hangover.Part.III.2013.DVDRip.X264-SPARKS.srt
Processing file: The.Hangover.UNRATED.720p.BluRay.x264-REFiNED.eng.srt
Processing file: The.Happytime.Murders.2018.1080p.Bluray.X264-EVO-HI.srt
Processing file: The.Haunted.Mansion.DVDRiP.XviD-BRUTUS.srt
Processing file: The.Haunting.In.Connecticut.2009.WEBRip.Amazon.srt
Processing file: The.Heat.2013.UNRATED.720p.BluRay.x264-SPARKS.srt
Skipping file: The.Heat.2013.UNRATED.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: The.Help.All.Bluray.Version.HI.srt
Skipping file: The.Help.All.Bluray.Version.HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Hills.Have.Eyes.II.2007.Unrated.1080p.BluRay.x264.anoXmous_eng.srt
Skipping file: The.Hills.Have.Eyes.II.2007.Unrated.1080p.BluRay.x264.anoXmous_eng.srt as all values in the 'speaker' column are NA's.
Processing file: The.Hills.Have.Eyes[2006][Unrated]DVDRIP[Eng]-aXXo.srt
Skipping file: The.Hills.Have.Eyes[2006][Unrated]DVDRIP[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: The.Hitcher[2007]DvDrip.AC3[Eng]-aXXo.srt
Processing file: The.Hobbit.The.Battle.of.the.Five.Armies.2014.720p.BluRay.x264-SPARKS.srt
Processing file: The.Hobbit.The.Desolation.Of.Smaug.2013.BRRip.XViD-juggs.Hi.srt
Processing file: The.Holiday.2006.720p.Bluray.x264.anoXmous_eng.srt
Processing file: The.Host.2013.720p.BluRay.x264.YIFY.srt
Processing file: The.House.with.a.Clock.in.Its.Walls.2018.1080p.WEB-DL.DD5.1.H264-FGT.srt
Processing file: The.Hundred-Foot.Journey.2014.720p.BluRay.x264-SPARKS.srt
Processing file: The.Hunger.Games.Catching.Fire.2013.BluRay.720p.x264.AC3-HDWinG.srt
Skipping file: The.Hunger.Games.Catching.Fire.2013.BluRay.720p.x264.AC3-HDWinG.srt as all values in the 'speaker' column are NA's.
Processing file: The.Hunger.Games.Mockingjay.Part.1.2014.720p.BluRay.x264-SPARKS.srt
Processing file: The.Hustle.2019.720p.HDCAM-1XBET-HI.srt
Skipping file: The.Hustle.2019.720p.HDCAM-1XBET-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Ice.Harvest[2005]DvDrip.AC3[Eng]-aXXo.srt
Skipping file: The.Ice.Harvest[2005]DvDrip.AC3[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: The.Identical.2014.720p.BluRay.x264-ROVERS-HI.srt
Processing file: The.Ides.of.March.2011.BluRay.english-psdh.srt
Processing file: The.Intruder.2019.HDRip.AC3.x264-CMRG-HI.srt
Processing file: the.invention.of.lying.2009.merry.xmas.bdrip.xvid-imbt.HI.srt
Processing file: The.Island.2005.1080p.BluRay.x264.DTS-FGT.srt
Processing file: The.Italian.Job.2003.1080p.BrRip.x264.YIFY.Hi.srt
Skipping file: The.Italian.Job.2003.1080p.BrRip.x264.YIFY.Hi.srt as all values in the 'speaker' column are NA's.
Processing file: The.Jacket.2005.720p.BluRay.x264.YIFY2.srt
Skipping file: The.Jacket.2005.720p.BluRay.x264.YIFY2.srt as all values in the 'speaker' column are NA's.
Processing file: The.Judge.2014.720p.BluRay.x264-SPARKS.srt
Processing file: The.Kid.Who.Would.Be.King.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: The.Kingdom.2007.1080p.BluRay.DTS.x264-WiKi.hi.srt
Processing file: The.Kings.Speech.2010.BRRip.XviD.AC3-TiMPE.ENG.srt
Skipping file: The.Kings.Speech.2010.BRRip.XviD.AC3-TiMPE.ENG.srt as all values in the 'speaker' column are NA's.
Processing file: The.Kitchen.2019.720p.BluRay.x264-DRONES-HI.srt
Processing file: The.Ladies.Man.2000.1080p.WEBRip.DD5.1.x264-FGT.en.sdh.srt
Skipping file: The.Ladies.Man.2000.1080p.WEBRip.DD5.1.x264-FGT.en.sdh.srt as all values in the 'speaker' column are NA's.
Processing file: The.Ladykillers.2004.1080p.WEBRip.DD5.1.x264-NTb.HI.eng.srt
Processing file: The.Lake.House.2006.720p.Bluray.AC3.x264-UNit3D-sdh.srt
Processing file: The.Last.Exorcism.Part.II.2013.UNRATED.720p.Bluray.x264-BLOW.srt
Skipping file: The.Last.Exorcism.Part.II.2013.UNRATED.720p.Bluray.x264-BLOW.srt as all values in the 'speaker' column are NA's.
Processing file: The.Last.Full.Measure.2019.720p.BluRay.x264.AAC-.YTS.LT.-HI.srt
Skipping file: The.Last.Full.Measure.2019.720p.BluRay.x264.AAC-.YTS.LT.-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Last.Samurai.2003.720p.Blu-Ray.x264.DTS.PRoDJi-HI.srt
Skipping file: The.Last.Samurai.2003.720p.Blu-Ray.x264.DTS.PRoDJi-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Lazarus.Effect.2015.720p.BluRay.x264-iNFAMOUS.srt
Processing file: The.League.of.Extraordinary.Gentlemen1.srt
Skipping file: The.League.of.Extraordinary.Gentlemen1.srt as all values in the 'speaker' column are NA's.
Processing file: The.League.of.Extraordinary.Gentlemen2.srt
Skipping file: The.League.of.Extraordinary.Gentlemen2.srt as all values in the 'speaker' column are NA's.
Processing file: The.Lincoln.Lawyer.2011.2160p.UHD.BluRay.x265-WhiteRhino.sdh.eng.srt
Processing file: The.Lizzie.McGuire.Movie.2003.WEB-DL.DSNP.srt
Processing file: The.Loft.2014.1080p.BluRay.AC3.x264-ETRG-eng.srt
Skipping file: The.Loft.2014.1080p.BluRay.AC3.x264-ETRG-eng.srt as all values in the 'speaker' column are NA's.
Processing file: The.Lone.Ranger.2013.720p.BluRay.DTS.x264-PublicHD.srt
Processing file: The.Longest.Ride.2015.720p.BluRay.x264-SPARKS.HI.srt
Processing file: The.Longest.Yard.2005.1080p.WEBRip.x264-RARBG.srt
Processing file: The.Lookout[2007]DvDrip[Eng]-aXXo.srt
Skipping file: The.Lookout[2007]DvDrip[Eng]-aXXo.srt as all values in the 'speaker' column are NA's.
Processing file: The.Lucky.One.2012.720p.BluRay.X264-AMIABLE.srt
Text not found in sentences: Bye, Mom. - Need to give the kid some room to breathe.   
Processing file: The.Man.2005.720p.WEB.alfaHD.HI.srt
Skipping file: The.Man.2005.720p.WEB.alfaHD.HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Man.from.U.N.C.L.E.2015.720p.BluRay.x264-SPARKS.HI.srt
Processing file: The.Man.with.the.Iron.Fists.2012.UNRATED.720p.BluRay.X264-AMIABLE.eng.srt
Processing file: The.Marine.UNRATED.DVDRip.XviD-NeDiVx.srt
Skipping file: The.Marine.UNRATED.DVDRip.XviD-NeDiVx.srt as all values in the 'speaker' column are NA's.
Processing file: The.Master.of.Disguise.2002.1080p.WEB.H264-DiMEPiECE.sdh.en.srt
Skipping file: The.Master.of.Disguise.2002.1080p.WEB.H264-DiMEPiECE.sdh.en.srt as all values in the 'speaker' column are NA's.
Processing file: The.Matrix.Reloaded.2003.720p.BrRip.264.YIFY.srt
Processing file: The.Matrix.Revolutions.2003.1080p.BluRay.x264-CtrlHD.-sdh.srt
Processing file: The.Maze.Runner.2014.720p.BluRay.x264-SPARKS.srt
Processing file: The.Mechanic.2011.720p.BRRip.XviD.AC3-FLAWL3SS.srt
Processing file: The.Meg.2018.srt
Processing file: The.Messengers.2007.720p.BluRay.DTS.x264-CtrlHD-SDH.srt
Processing file: The.Mexican.2001.720p.BluRay.DTS.x264-RuDE.EN.srt
Skipping file: The.Mexican.2001.720p.BluRay.DTS.x264-RuDE.EN.srt as all values in the 'speaker' column are NA's.
Processing file: The.Missing.2003.1080p.BluRay.H264.AAC-RARBG_English.srt
Processing file: The.Mist.2007.DvDRip.Eng-FxM.en.HI.srt
Processing file: The.Monuments.Men.2014.720p.BluRay.x264-BLOW-HI.srt
Processing file: The.Mortal.Instruments.City.of.Bones.2013.REAL.720p.BluRay.x264-GECKOS.srt
Skipping file: The.Mortal.Instruments.City.of.Bones.2013.REAL.720p.BluRay.x264-GECKOS.srt as all values in the 'speaker' column are NA's.
Processing file: The.Mule.2018.1080p.BluRay.x264-DRONES-HI.srt
Skipping file: The.Mule.2018.1080p.BluRay.x264-DRONES-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Mummy-Tomb.Of.The.Dragon.Emperor[2008]DvDrip-aXXo.en.HI.srt
Processing file: The.Mummy.2017.720p.BluRay.x264-GECKOS.HI.srt
Processing file: The.Mummy.Returns.-.English.srt
Skipping file: The.Mummy.Returns.-.English.srt as all values in the 'speaker' column are NA's.
Processing file: The.Muppets.2011.720p.BluRay.x264-SPARKS.Hi.srt
Processing file: The.Musketeer.2001.Eng.SDH.Synced.to.GER.BD.srt
Skipping file: The.Musketeer.2001.Eng.SDH.Synced.to.GER.BD.srt as all values in the 'speaker' column are NA's.
Processing file: The.Nanny.Diaries.srt
Skipping file: The.Nanny.Diaries.srt as all values in the 'speaker' column are NA's.
Processing file: The.New.Guy.2002.WEB-DLRip.720p.srt
Skipping file: The.New.Guy.2002.WEB-DLRip.720p.srt as all values in the 'speaker' column are NA's.
Processing file: The.Next.Three.Days.2010.720p.BRRip.XviD.AC3-ViSiON.srt
Skipping file: The.Next.Three.Days.2010.720p.BRRip.XviD.AC3-ViSiON.srt as all values in the 'speaker' column are NA's.
Processing file: the.night.listener.2006.720p.bluray.x264-psychd.srt
Skipping file: the.night.listener.2006.720p.bluray.x264-psychd.srt as all values in the 'speaker' column are NA's.
Processing file: The.Ninth.Gate.1999.720p.BRRip.x264.AAC-ABG.srt
Skipping file: The.Ninth.Gate.1999.720p.BRRip.x264.AAC-ABG.srt as all values in the 'speaker' column are NA's.
Processing file: The.November.Man.2014.720p.BluRay.x264-SPARKS.srt
Skipping file: The.November.Man.2014.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: The.Number.23[2007][Unrated.Edition][DvDrip[Eng]-aXXo.srt
Processing file: The.Nun.2018.720p.BluRay.x264-GECKOS-HI.srt
Processing file: The.Nutcracker.And.The.Four.Realms.2018.BRRip.XviD.AC3-EVO-HI.srt
Processing file: The.Odd.Life.of.Timothy.Green.2012.720p.BluRay.x264-ALLiANCE.eng.srt
Processing file: The.One.2001.720p.BrRip.x264.YIFY.srt
Skipping file: The.One.2001.720p.BrRip.x264.YIFY.srt as all values in the 'speaker' column are NA's.
Processing file: The.Other.Guys.2010.-FraMeSToR_en.sdh.srt
Processing file: The.Other.Woman.2014.720p.BluRay.x264.DTS-RARBG-HI.srt
Processing file: The.Others.srt
Processing file: The.Pacifier.DVDRip.XviD-DiAMOND.srt
Skipping file: The.Pacifier.DVDRip.XviD-DiAMOND.srt as all values in the 'speaker' column are NA's.
Processing file: The.Patriot.2000.Extended.Cut.1080p.BluRay.x264.anoXmous_eng[SDH].srt
Processing file: The.Perfect.Guy.2015.720p.BluRay.x264-GECKOS-HI.srt
Processing file: The.Perfect.Holiday.2007.1080p.WEBRip.x264-RARBG.srt
Processing file: The.Pledge.2001.WEB-DL.NF.en.srt
Processing file: The.Possession.of.Hannah.Grace.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: The.Predator.2018.720p.HC.HDRip.X264.AC3-EVO-HI.srt
Processing file: The.Prince.and.Me.2004.720p.BluRay.x264-x0r.HI.eng.srt
Processing file: The.Princess.Diaries.2.Royal.Engagement.2004.720p.BluRay.x264-PSYCHD.srt
Skipping file: The.Princess.Diaries.2.Royal.Engagement.2004.720p.BluRay.x264-PSYCHD.srt as all values in the 'speaker' column are NA's.
Processing file: The.Prodigy.2019.1080p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: The.Promise.2016.720p.BluRay.x264-DRONES.HI.srt
Processing file: The.Punisher.2004.BluRay.720p.H264-eng.srt
Processing file: The.Purge.2013.720p.WEB-DL.H264.LiNE-TST.srt
Processing file: The.Purge.Anarchy.2014.720p.BluRay.x264-SPARKS.srt
Processing file: The.Pursuit.of.Happyness.2006.DVD5.720p.BluRay.x264-REVEiLLE.en.srt
Skipping file: The.Pursuit.of.Happyness.2006.DVD5.720p.BluRay.x264-REVEiLLE.en.srt as all values in the 'speaker' column are NA's.
Processing file: The.Pyramid.2014.720p.BluRay.x264-GECKOS.srt
Processing file: The.Raven.2012.720p.BRRip.x264.AAC-LEGi0N.English.srt
Processing file: The.Reaping(2007)DvdRip[MiNdSkiN]1337x.en.HI.srt
Processing file: The.Recruit.srt
Processing file: The.Ring.2.[2005].DVDRip.XviD-BLiTZKRiEG.srt
Skipping file: The.Ring.2.[2005].DVDRip.XviD-BLiTZKRiEG.srt as all values in the 'speaker' column are NA's.
Processing file: The.Rite.DVDRip.XviD-ARROW.srt
Processing file: The.Rocker[2008]DvDrip-aXXo.en.HI.srt
Processing file: The.Roommate.2011.BRRip.Xvid {1337x}-Noir-EN+HI.srt
Processing file: The.Ruins.2008.WEB-DL.NF.en.srt
Skipping file: The.Ruins.2008.WEB-DL.NF.en.srt as all values in the 'speaker' column are NA's.
Processing file: The.rules.of.attraction.2002.DVDRip.XviD-DiRGE.EN.srt
Skipping file: The.rules.of.attraction.2002.DVDRip.XviD-DiRGE.EN.srt as all values in the 'speaker' column are NA's.
Processing file: The.Santa.Clause.3.The.Escape.Clause.2006.WEB-DL.DSNP.srt
Processing file: The.Second.Best.Exotic.Marigold.Hotel.2015.720p.BluRay.x264-GECKOS-HI.srt
Processing file: The.Secret.Life.of.Walter.Mitty.2013.720p.BluRay.x264-SPARKS.srt
Skipping file: The.Secret.Life.of.Walter.Mitty.2013.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: The.Sentinel.DVDRip.XviD-DiAMOND.HI.srt
Skipping file: The.Sentinel.DVDRip.XviD-DiAMOND.HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Shaggy.Dog[2006]DvDrip.AC3[Eng]-aXXo.srt
Processing file: The.Single.Moms.Club.2014.BRRip.XViD.juggs[ETRG].srt
Skipping file: The.Single.Moms.Club.2014.BRRip.XViD.juggs[ETRG].srt as all values in the 'speaker' column are NA's.
Processing file: The.Sisterhood.of.the.Traveling.Pants.2.DVDRip.ENG SUBS.srt
Processing file: The.Sisterhood.of.the.Traveling.Pants.2005.1080p.WEBRip.x264-RARBG_English.srt
Processing file: The.Sixth.Sense.[1999].DVDRip.Xvid.Blood.srt
Skipping file: The.Sixth.Sense.[1999].DVDRip.Xvid.Blood.srt as all values in the 'speaker' column are NA's.
Processing file: The.Skeleton.Key.2005.720p.BrRip.x264.YIFY.srt
Processing file: The.Skulls.2000.DVDRip.XviD-SAPHiRE.srt
Skipping file: The.Skulls.2000.DVDRip.XviD-SAPHiRE.srt as all values in the 'speaker' column are NA's.
Processing file: The.Social.Network.2010.2160p.BluRay.REMUX.HEVC.DTS-HD.MA.TrueHD.7.1.Atmos-FGT.en.srt
Skipping file: The.Social.Network.2010.2160p.BluRay.REMUX.HEVC.DTS-HD.MA.TrueHD.7.1.Atmos-FGT.en.srt as all values in the 'speaker' column are NA's.
Processing file: The.Space.Between.Us.2017.720p.BluRay.x264-DRONES.HI.srt
Processing file: The.Spirit.2008.1080p.BluRay.x264.anoXmous_eng.srt
Processing file: The.Spy.Who.Dumped.Me.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: The.Stepford.Wives.2004.WEBRip.x264-ION10.srt
Processing file: The.Strangers.Prey.at.Night.2018.720p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Skipping file: The.Strangers.Prey.at.Night.2018.720p.WEB-DL.DD5.1.H264-CMRG-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.Strangers.UNRATED.720p.BluRay.x264-SEPTiC.srt
Processing file: The.Sum.of.All.Fears.2002.REMASTERED.1080p.BluRay.x264.TrueHD.5.1-SWTYBLZ.srt
Processing file: The.Sun.Is.Also.a.Star.2019.720p.HDCAM-1XBET-HI.srt
Skipping file: The.Sun.Is.Also.a.Star.2019.720p.HDCAM-1XBET-HI.srt as all values in the 'speaker' column are NA's.
Processing file: The.sweetest.thing.2002.BRRip.720p.srt
Skipping file: The.sweetest.thing.2002.BRRip.720p.srt as all values in the 'speaker' column are NA's.
Processing file: the.switch.srt
Processing file: The.Taking.of.Pelham.1.2.3.2009.1080p.BluRay.DTS.x264-WiKi.srt
Processing file: The.Texas.Chainsaw.Massacre.2003.1080p.Bluray.X264-BARC0DE_English_SDH.srt
Processing file: The.Three.Musketeers.2011.720p.BrRip.x264.YIFY.en.hi.srt
Processing file: The.Three.Stooges.BRrip.720p-HiGH.srt
Text not found in sentences: What about Sister Mary-Mengele?
 
Processing file: The.Time.Machine.spellchecked.srt
Skipping file: The.Time.Machine.spellchecked.srt as all values in the 'speaker' column are NA's.
Processing file: the.time.travelers.wife.dvdrip.xvid-imbt.srt
Processing file: The.To.Do.List.2013.BDRip.X264-ALLiANCE-SDH.srt
Processing file: The.Town.EXTENDED.2010.720p.BRRip.XviD.AC3-FLAWL3SS.srt
Processing file: The.Twilight.Saga.Breaking.Dawn.Part.1.2011.720p.BluRay.x264-SPARKS English.srt
Processing file: The.Twilight.Saga.Breaking.Dawn.Part.2.2012.720p.BluRay.x264-GECKOS.eng.srt
Skipping file: The.Twilight.Saga.Breaking.Dawn.Part.2.2012.720p.BluRay.x264-GECKOS.eng.srt as all values in the 'speaker' column are NA's.
Processing file: The.Unborn-iKA.srt
Processing file: The.Visit.2015.720p.BluRay.x264-Replica.HI.srt
Processing file: The.Vow.2012.720p.BluRay.x264-Felony.english.srt
Processing file: The.Wall.2017.BDRip.x264-DRONES.SDH.srt
Processing file: The.Wash.2001.1080p.WEBRip.x264-RARBG.srt
Processing file: The.Way.Back.2010.1080p.BrRip.x264.BOKUTOX.srt
Skipping file: The.Way.Back.2010.1080p.BrRip.x264.BOKUTOX.srt as all values in the 'speaker' column are NA's.
Processing file: The.Wedding.Date.2005.1080p.HDDVD.x264-FSiHD.ENG_HI.srt
Processing file: The.Wedding.Planner.2001.WEBRip.Amazon.srt
Processing file: The.Wedding.Ringer.2015.BRRip.XviD.AC3-RARBG.srt
Processing file: The.Whole.Nine.Yards.2000.720p.BluRay.X264-AMIABLE-HI.srt
Processing file: The.Wolf.of.Wall.Street.2013.720p.BluRay.X264-AMIABLE-HI.srt
Processing file: The.Wolverine.2013.EXTENDED.720p.BluRay.x264-SPARKS.srt
Skipping file: The.Wolverine.2013.EXTENDED.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: The.Worlds.End.2013.720p.BluRay.x264-SPARKS.srt
Processing file: The.X.Files.I.Want.To.Believe.(Extended version).2008.720p.BluRay.DTS.x264-SiNNERS{ENG}.srt
Processing file: The.Zookeepers.Wife.2017.1080p.BluRay.x264-GECKOS.srt
Processing file: TheAmerican_2010_FXG.EN.srt
Processing file: TheSitterUNRATED_Diamond.srt
Processing file: They.Sie.Kommen.2002.Open.Matte.German.DD51D.DL.1080p.AmazonHD.x264-iND_full_SDH_[eng].srt
Processing file: the_bourne_supremacy_hdrip_x264_uSk.english.srt
Skipping file: the_bourne_supremacy_hdrip_x264_uSk.english.srt as all values in the 'speaker' column are NA's.
Processing file: the_insider-en.srt
Skipping file: the_insider-en.srt as all values in the 'speaker' column are NA's.
Processing file: The_last_castle_englhi.srt
Skipping file: The_last_castle_englhi.srt as all values in the 'speaker' column are NA's.
Processing file: The_Last_Song_(2010).DVDRip.AC3.XviD.English.srt
Skipping file: The_Last_Song_(2010).DVDRip.AC3.XviD.English.srt as all values in the 'speaker' column are NA's.
Processing file: the_watcher_englhi.srt
Skipping file: the_watcher_englhi.srt as all values in the 'speaker' column are NA's.
Processing file: thick-pop-cd1-sdh.en.srt
Processing file: thick-pop-cd2-sdh.en.srt
Processing file: Think Like a Man 2012 BluRay Bdrip Brrip x264 1080p 720p 480p.Hi.srt
Processing file: Think.Like.A.Man.Too.2014.720p.BluRay.x264-BLOW.srt
Processing file: Thir13en.Ghosts.2001.BluRay.srt
Skipping file: Thir13en.Ghosts.2001.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: This.Christmas.2007.BluRay.H264.AAC-RARBG.en.srt
Processing file: This.is.40.2012.UNRATED.720p.BluRay.X264-ALLiANCE.srt
Skipping file: This.is.40.2012.UNRATED.720p.BluRay.X264-ALLiANCE.srt as all values in the 'speaker' column are NA's.
Processing file: This.Is.It.DVDRip.XviD-ESPiSE-SDH.CD1.srt
Processing file: This.Is.It.DVDRip.XviD-ESPiSE-SDH.CD2.srt
Processing file: This.is.the.End.2013.720p.BluRay.x264-SPARKS.srt
Skipping file: This.is.the.End.2013.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: This.Is.Where.I.Leave.You.2014.720p.BluRay.x264-BLOW.srt
Processing file: This.Means.War.2012.UNRATED.720p.Bluray.x264.FULL.srt
Processing file: Thomas.and.the.Magic.Railroad.2000.1080p.WEBRip.x264-RARBG.2.srt
Processing file: Thor [2011].srt
Processing file: Thor.Ragnarok.2017.720p.BluRay.srt
Processing file: Thor.The.Dark.World.2013.720p.HDRip.XviD-AQOS-hi.srt
Processing file: Thoroughbreds.2017.720p.BluRay.srt
Processing file: Thunderbirds.2004.WEB-DL.x264-ION10.srt
Skipping file: Thunderbirds.2004.WEB-DL.x264-ION10.srt as all values in the 'speaker' column are NA's.
Processing file: timpe-grindhouse.srt
Processing file: tlf-nda.en.srt
Skipping file: tlf-nda.en.srt as all values in the 'speaker' column are NA's.
Processing file: Tolkien.2019.720p.WEBRip.800MB.x264-GalaxyRG.srt
Processing file: tom yum goong cd 1.srt
Skipping file: tom yum goong cd 1.srt as all values in the 'speaker' column are NA's.
Processing file: tom yum goong cd 2.srt
Skipping file: tom yum goong cd 2.srt as all values in the 'speaker' column are NA's.
Processing file: Tomb.Raider.2018.720p.WEB-DL.H264.AC3-EVO (CHI).srt
Skipping file: Tomb.Raider.2018.720p.WEB-DL.H264.AC3-EVO (CHI).srt as all values in the 'speaker' column are NA's.
Processing file: Tomcats.2001.1080p.BluRay.srt
Processing file: Tomorrowland (2015) SDH.srt
Processing file: Tooth Fairy.[2010].DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Skipping file: Tooth Fairy.[2010].DVDRIP.INTEL.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Top.Five.2014.WEB-DL.x264-RARBG.srt
Skipping file: Top.Five.2014.WEB-DL.x264-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: Total Recall 2012 Ext Directors Cut BluRay 1080p DD5.srt
Processing file: Tower Heist 2011 BluRay Bdrip x264 1080p 720p.Hi.srt
Processing file: Town.and.Country.2001.WEBRip.x264-RARBG.srt
Processing file: Traffik.2018.720p.BluRay.x264-DRONES-HI.srt
Processing file: Training.Day.2001.DVDRip.XviD-DiSSOLVE.srt
Skipping file: Training.Day.2001.DVDRip.XviD-DiSSOLVE.srt as all values in the 'speaker' column are NA's.
Processing file: Trainwreck.2015.THEATRICAL.iNTERNAL.BDRip.x264-GHOULS.Hi.srt
Processing file: Transcendence.2014.1080p.WEB-DL.DD5.1.H264-RARBG.srt
Skipping file: Transcendence.2014.1080p.WEB-DL.DD5.1.H264-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: Transformers Revenge of the Fallen.[2009].RETAIL.DVDRIP.XVID.[Eng]-DUQA.srt
Processing file: Transformers.Age.of.Extinction.2014.HDRip.XViD.AC3-juggs[ETRG].srt
Processing file: Transformers.Dark.of.the.Moon.2011.WEBRip.Amazon.srt
Processing file: Transformers.The.Last.Knight.2017.720p.BluRay.X264-AMIABLE.HI.srt
Processing file: Transporter.2.2005.DVDRip.XviD-ViP3R.srt
Skipping file: Transporter.2.2005.DVDRip.XviD-ViP3R.srt as all values in the 'speaker' column are NA's.
Processing file: Trapped (2002).en.srt
Skipping file: Trapped (2002).en.srt as all values in the 'speaker' column are NA's.
Processing file: Tristan.and.Isolde[2006]DvDrip[Eng]-aXXo.en.srt
Skipping file: Tristan.and.Isolde[2006]DvDrip[Eng]-aXXo.en.srt as all values in the 'speaker' column are NA's.
Processing file: Tron.Legacy.2010.720p.BDRip.XviD.srt
Processing file: Trouble with the Curve 2012 BluRay Bdrip Brrip x264 1080p 720p 480p.srt
Processing file: Troy (2004)xvid.srt
Processing file: True.Grit.2010.SCR.srt
Skipping file: True.Grit.2010.SCR.srt as all values in the 'speaker' column are NA's.
Processing file: Truth About Charlie (2002).DVDRip.XviD-DEiTY.English [cc].srt
Skipping file: Truth About Charlie (2002).DVDRip.XviD-DEiTY.English [cc].srt as all values in the 'speaker' column are NA's.
Processing file: Truth About Charlie (2002).DVDRip.XviD-DEiTY.English.srt
Skipping file: Truth About Charlie (2002).DVDRip.XviD-DEiTY.English.srt as all values in the 'speaker' column are NA's.
Processing file: Truth.or.Dare.2018.REPACK.720p.WEB-DL.X264-CPG-HI.srt
Processing file: Tully.2018.1080p.WEB-DL.DD5.1.srt
Processing file: Twilight Saga New Moon_DVDrip_enHI.srt
Processing file: Twilight.2008.DVDRIP.XviD-ZEKTORM.srt
Processing file: Twisted 2004 NTSC.srt
Processing file: twiz-arthur-a.srt
Processing file: twiz-arthur-b.srt
Processing file: Two.Can.Play.That.Game.2001.720p.BluRay.x264-PSYCHD.Hi.srt
Processing file: Two.Weeks.Notice.2002.720p.BluRay.X264-AMIABLE-sdh.srt
Processing file: U-571.2000.720p.BrRip.x264.srt
Skipping file: U-571.2000.720p.BrRip.x264.srt as all values in the 'speaker' column are NA's.
Processing file: Ultraviolet (Unrated).srt
Skipping file: Ultraviolet (Unrated).srt as all values in the 'speaker' column are NA's.
Processing file: Unaccompanied.Minors.2006.1080p.WEBRip.x264-RARBG.srt
Processing file: Unbreakable.2000.MULTi.1080p.Bluray.HDLight.x264-colored-HI.srt
Skipping file: Unbreakable.2000.MULTi.1080p.Bluray.HDLight.x264-colored-HI.srt as all values in the 'speaker' column are NA's.
Processing file: UNBROKEN - PATH TO REDEMPTION HI.srt
Skipping file: UNBROKEN - PATH TO REDEMPTION HI.srt as all values in the 'speaker' column are NA's.
Processing file: Unbroken.2014.720p.BluRay.X264-AMIABLE.srt
Processing file: Uncle.Drew.2018.DVDRip.XviD.AC3-EVO-HI.srt
Text not found in sentences: Uncle Drew and the ladies?   
Processing file: Under The Tuscan Sun DVDRip XViD-DVL.srt
Processing file: Underclassman.2005.720p.WEBRip.x264.AAC-[YTS.MX].srt
Skipping file: Underclassman.2005.720p.WEBRip.x264.AAC-[YTS.MX].srt as all values in the 'speaker' column are NA's.
Processing file: Undercover Brother[2002]DVDRip[Eng]-NuMy.srt
Text not found in sentences: Conspiracy Brother: Y'all don't give a shit about me!
 
Processing file: Underworld Rise of the Lycans 2009 BDRip 1080p x265 AC3 6Ch D3FiL3R.srt
Processing file: Underworld.Awakening.2012.PROPER.720p.BluRay.x264-ALLiANCE.english.srt
Processing file: Underworld.Blood.Wars.2016.720p.BluRay.x264-GECKOS.HI.srt
Processing file: Underworld.Eng (SDH).srt
Processing file: Underworld.Evolution.2006.DVDRip.XviD.AC3.iNT-JUPiT.CD1.eng.srt
Skipping file: Underworld.Evolution.2006.DVDRip.XviD.AC3.iNT-JUPiT.CD1.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Underworld.Evolution.2006.DVDRip.XviD.AC3.iNT-JUPiT.CD2.eng.srt
Skipping file: Underworld.Evolution.2006.DVDRip.XviD.AC3.iNT-JUPiT.CD2.eng.srt as all values in the 'speaker' column are NA's.
Processing file: Undiscovered.2005.1080p.WEBRip.x264-RARBG.srt
Processing file: Undisputed.I.2002.DVDRip.XviD-NoGrp.srt
Skipping file: Undisputed.I.2002.DVDRip.XviD-NoGrp.srt as all values in the 'speaker' column are NA's.
Processing file: Unfaithful 2002 DVDRip Xvid LKRG.srt
Processing file: Unfinished.Business.2015.720p.BluRay.x264-GECKOS.srt
Processing file: Unforgettable.2017.1080p.BluRay.x264-DRONES.srt
Processing file: Unfriended.2014.WEB-DL.x264-RARBG.srt
Skipping file: Unfriended.2014.WEB-DL.x264-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: Unfriended.Dark.Web.2018.V2.HC.HDRip.XviD.AC3-EVO-HI.srt
Processing file: United.93[2006]DvDrip[Eng][H.I]-aXXo.srt
Processing file: Unknown[2011]DvDrip[Eng]-FXG.HI.srt
Processing file: Unleashed.2005.1080p.BrRip.x264.srt
Processing file: Unplanned (2019) [BluRay] [1080p] [YTS.LT].srt
Processing file: UNRATED.DVDRip.srt
Processing file: Unsane.2018.1080p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Unstoppable.2010.720p.BluRay.x264.YIFY.HI.srt
Processing file: Upgrade.2018.720p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: Us.2019.720p.BluRay.x264-GECKOS-HI.srt
Processing file: V For Vendetta.srt
Processing file: Vacancy.2007.720p.BluRay.srt
Processing file: Vacation.2015.720p.BluRay.x264-DRONES-HI.srt
Processing file: Valentine english for the hearing imperaid.srt
Processing file: Valkyrie.2008.1080p.BrRip.x264.YIFY.srt
Processing file: Vampire.Academy.2014.720p.BluRay.x264-SPARKS-HI.srt
Processing file: Vampires Suck (HD).srt
Processing file: Van Helsing - English Hearing Impaired (25FPS).srt
Processing file: Vanity Fair 2004 PAL.srt
Processing file: Vantage.Point.2008.BluRay.x264.DTS-FGT.en.srt
Skipping file: Vantage.Point.2008.BluRay.x264.DTS-FGT.en.srt as all values in the 'speaker' column are NA's.
Processing file: Venom.2018.1080p.BluRay.x264-.YTS.AM.HI.srt
Processing file: Vertical.Limit.2000.1080p.BluRay.H264.srt
Processing file: Vice.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Vicky.Cristina.Barcelona.2008.Bluray.english-sdh.srt
Processing file: View From The Top.srt
Skipping file: View From The Top.srt as all values in the 'speaker' column are NA's.
Processing file: vmt-post-xvid.en.srt
Skipping file: vmt-post-xvid.en.srt as all values in the 'speaker' column are NA's.
Processing file: VOMiT (USA version 84 mins).srt
Skipping file: VOMiT (USA version 84 mins).srt as all values in the 'speaker' column are NA's.
Processing file: W.[2008]DvDrip-aXXo.en.HI.srt
Processing file: Walk Hard - The Dewey Cox Story (2007) (Theatrical Cut)-SDH.srt
Processing file: Walk.the.Line.Extended.Cut.2005.1080p.BluRay.H264.AAC-RARBG-eng.srt
Processing file: Walking.Tall.2004.720p.BluRay.x264.VPPV.srt
Processing file: Wall Street 2 Money Never Sleeps.2010..ALL .Bluray..BRRip.720p.and.480p.srt
Text not found in sentences: I'm taking a huge hit on the loft, I just sold my bike for nothing and now, again, I'm writing you a check, Mom.
 
Processing file: Wanderlust 2012 BluRay Bdrip Brrip x264 1080p 720p 480p.Hi.srt
Processing file: Wanted.2008.BluRay.1080p.DTS.x264.dxva-EuReKA.ENG_HI.srt
Processing file: War Of The Worlds.srt
Processing file: War.Room.2015.PROPER.1080p.BluRay.x264-DRONES-HI.srt
Processing file: Warm.Bodies.2013.HDRip.x264.AC3-FooKaS.srt
Processing file: Warrior (2011).hearingaid.utf8.en.srt
Processing file: War[2007]DvDrip[Eng]-aXXo.HI.en.srt
Skipping file: War[2007]DvDrip[Eng]-aXXo.HI.en.srt as all values in the 'speaker' column are NA's.
Processing file: Watchmen.DC.720p.Bluray.x264-CBGB.srt
Text not found in sentences: Police!   
Processing file: Water for Elephants[2011]DVDRip XviD-ExtraTorrentRG.Hi.srt
Processing file: We Were Soldiers-eng.srt
Processing file: We.Are.Your.Friends.2015.PROPER.720p.BluRay.X264-AMIABLE.HI.srt
Skipping file: We.Are.Your.Friends.2015.PROPER.720p.BluRay.X264-AMIABLE.HI.srt as all values in the 'speaker' column are NA's.
Processing file: We.Bought.a.Zoo.2011.DVDRip.XviD-NeDiVx.cd1.english.srt
Skipping file: We.Bought.a.Zoo.2011.DVDRip.XviD-NeDiVx.cd1.english.srt as all values in the 'speaker' column are NA's.
Processing file: We.Bought.a.Zoo.2011.DVDRip.XviD-NeDiVx.cd2.english.srt
Skipping file: We.Bought.a.Zoo.2011.DVDRip.XviD-NeDiVx.cd2.english.srt as all values in the 'speaker' column are NA's.
Processing file: We.Own.the.Night.2007.720p.BluRay.DTS.x264-ESiR-hi.srt
Processing file: Wedding.Crashers.2005.UNRATED.1080p.BluRay.x264-CiNEFiLE.ENG_HI.srt
Processing file: Welcome To Mooseport CD 1.srt
Skipping file: Welcome To Mooseport CD 1.srt as all values in the 'speaker' column are NA's.
Processing file: Welcome To Mooseport CD 2.srt
Skipping file: Welcome To Mooseport CD 2.srt as all values in the 'speaker' column are NA's.
Processing file: Welcome.to.Marwen.2019.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Were.the.Millers.2013.EXTENDED.720p.BluRay.x264.srt
Processing file: What a Girl Wants (2003) 720p WEB-DL.en SDH.srt
Processing file: What Lies Beneath.srt
Skipping file: What Lies Beneath.srt as all values in the 'speaker' column are NA's.
Processing file: What To Expect When Youre Expecting 2012 BluRay Bdrip Brrip x264 1080p 720p 480p.Hi.srt
Processing file: what women want.srt
Skipping file: what women want.srt as all values in the 'speaker' column are NA's.
Processing file: What.Happens.In.Vegas[2008]DvDrip-aXXo.srt
Processing file: What.Men.Want.2019.1080p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Skipping file: What.Men.Want.2019.1080p.WEB-DL.DD5.1.H264-CMRG-HI.srt as all values in the 'speaker' column are NA's.
Processing file: What.Planet.Are.You.From.2000.720p.BluRay.x264-SNOW-HI.srt
Skipping file: What.Planet.Are.You.From.2000.720p.BluRay.x264-SNOW-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Whatever.It.Takes.2000.WEB-DL.NONTON01.srt
Skipping file: Whatever.It.Takes.2000.WEB-DL.NONTON01.srt as all values in the 'speaker' column are NA's.
Processing file: Whats.the.Worst.That.Could.Happen.srt
Skipping file: Whats.the.Worst.That.Could.Happen.srt as all values in the 'speaker' column are NA's.
Processing file: Whats.Your.Number.2011.DvDRip.Xvid.EMPIrE.srt
Text not found in sentences: Oy! Hi, Mom, can I call you right back?
 
Processing file: When.A.Stranger.Calls.2006.BluRay.x264.AAC-[YTS.MX].en.srt
Text not found in sentences: Police are looking for links between the victims.
 
Processing file: When.the.Game.Stands.Tall.2014.720p.BluRay.x264-GECKOS.srt
Processing file: Where The Heart Is.srt
Skipping file: Where The Heart Is.srt as all values in the 'speaker' column are NA's.
Processing file: Where the Wild Things Are.[2009].DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Processing file: Where.The.Money.Is-vRs.srt
Processing file: Whered.You.Go.Bernadette.2019.1080p.WEB-DL.DD5.1.H264-CMRG-HI.srt
Processing file: Whip.It.2009.DvDrip.srt
Processing file: Whipped.2000.1080p.WEBRip.srt
Skipping file: Whipped.2000.1080p.WEBRip.srt as all values in the 'speaker' column are NA's.
Processing file: white noise.srt
Skipping file: white noise.srt as all values in the 'speaker' column are NA's.
Processing file: White.Boy.Rick.2018.720p.TS-1XBET-HI.srt
Processing file: White.Chicks.2004.UNRATED.1080p.WEBRip.x264-RARBG_English.srt
Processing file: White.House.Down.2013.720p.BDRip.LATiNO.ENG.XviD.AC3.English.SDH.srt
Processing file: White.Oleander.2002.720p.WEB-DL.DD5.1.H264-FGT.SDH.eng.srt
Processing file: Whiteout.[2009].DVDRIP.XVID.[Eng]-DUQA.srt
Processing file: Why Did I Get Married Too.[2010].DVDRIP.H264.[Eng]-DUQA.srt
Skipping file: Why Did I Get Married Too.[2010].DVDRIP.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Why.Him.2016.DVDRip.XviD.AC3-EVO.srt
Processing file: Wicker.Park.2004.WEBRip.x264-ION10.srt
Skipping file: Wicker.Park.2004.WEBRip.x264-ION10.srt as all values in the 'speaker' column are NA's.
Processing file: Widows.2018.HDRip.XviD.AC3-EVO-HI.srt
Processing file: Willard.2003.720p.BluRay.X264-AMIABLE-HI.srt
Skipping file: Willard.2003.720p.BluRay.X264-AMIABLE-HI.srt as all values in the 'speaker' column are NA's.
Processing file: Wimbledon.2004.DVDRip.XviD-DVL.srt
Skipping file: Wimbledon.2004.DVDRip.XviD-DVL.srt as all values in the 'speaker' column are NA's.
Processing file: Win a Date with Tad Hamilton!.srt
Skipping file: Win a Date with Tad Hamilton!.srt as all values in the 'speaker' column are NA's.
Processing file: Winchester.2018.1080p.WEB-DL.H264.AC3-EVO-HI.srt
Processing file: Windtalkers (2002).DVDRip.HI.cc.en.MGM.srt
Skipping file: Windtalkers (2002).DVDRip.HI.cc.en.MGM.srt as all values in the 'speaker' column are NA's.
Processing file: Winters.Tale.2014.720p.BluRay.x264.YIFY.srt
Processing file: Witless Protection .[2008].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Witless Protection .[2008].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Woman On Top.srt
Skipping file: Woman On Top.srt as all values in the 'speaker' column are NA's.
Processing file: Wonder.2017.720p.BluRay.x264-GECKOS.HI.srt
Processing file: Wonder.Boys.2000.720p.HDTV.x264-ESiR.srt
Processing file: Woody.Allen.Small.Time.Crooks.2000.1080p.BluRay.H264.AAC-RARBG.srt
Skipping file: Woody.Allen.Small.Time.Crooks.2000.1080p.BluRay.H264.AAC-RARBG.srt as all values in the 'speaker' column are NA's.
Processing file: World.War.Z.2013.UNRATED.720p.BluRay.x264-SPARKS.srt
Skipping file: World.War.Z.2013.UNRATED.720p.BluRay.x264-SPARKS.srt as all values in the 'speaker' column are NA's.
Processing file: Wrath of the Titans.[2012].DVDRIP.DIVX.[Eng]-DUQA.srt
Skipping file: Wrath of the Titans.[2012].DVDRIP.DIVX.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: wrong turn[2003]Xvid.Avi.NeRoZ.en.srt
Skipping file: wrong turn[2003]Xvid.Avi.NeRoZ.en.srt as all values in the 'speaker' column are NA's.
Processing file: ws.dvdrip.srt
Skipping file: ws.dvdrip.srt as all values in the 'speaker' column are NA's.
Processing file: X-Men 2 ;[2003];[1080p];[Shadowl0rd].ENG_HI.srt
Skipping file: X-Men 2 ;[2003];[1080p];[Shadowl0rd].ENG_HI.srt as all values in the 'speaker' column are NA's.
Processing file: X-Men Origins Wolverine.srt
Processing file: X-Men.Days.of.Future.Past.2014.720p.BluRay.X264-AMIABLE.srt
Skipping file: X-Men.Days.of.Future.Past.2014.720p.BluRay.X264-AMIABLE.srt as all values in the 'speaker' column are NA's.
Processing file: X-Men.First.Class.2011.720p.BRRip.x264.AAC-ViSiON.srt
Skipping file: X-Men.First.Class.2011.720p.BRRip.x264.AAC-ViSiON.srt as all values in the 'speaker' column are NA's.
Processing file: X-Men.The.Last.Stand.2006. 4K.HDR.2160p.BDRip Ita Eng x265-NAHOM.srt
Processing file: xXx 2002 3Li BluRay English (Hearing Impaired) - Extract BD.srt
Processing file: xXx.Return.of.Xander.Cage.2017.720p.BluRay.x264-GECKOS.HI.srt
Processing file: You.Again.720p.BluRay.srt
Skipping file: You.Again.720p.BluRay.srt as all values in the 'speaker' column are NA's.
Processing file: You.Got.Served.2004.1080p.WEB-DL.DD5.1.H264-FGT.srt
Processing file: You.Me.and.Dupree[2006]DvDrip[Eng]-aXXo.srt
Processing file: Your.Highness.2011.UNRATED.720p.BRRip.x264.AAC-ViSiON.srt
Text not found in sentences: You should swing from your hips, Brother.
 
Text not found in sentences: Brother, are you all right?
 
Processing file: Youre.Next.2011.1080p.BluRay.x264-GECKOS-sdh.srt
Processing file: Youth in Revolt.[2009].DVDRIP.INTEL.H264.[Eng]-DUQA.srt
Skipping file: Youth in Revolt.[2009].DVDRIP.INTEL.H264.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Zack And Miri Make A Porno.srt
Processing file: Zodiac.2007.Directors.Cut.iNTERNAL.1080p.BluRay.x264-MHQ_track1_eng.srt
Processing file: Zombieland.Double.Tap.2019.HDRip.HC.AC3.X264-CMRG-HI.srt
Processing file: Zombieland.[2009].DVDRIP.XVID.[Eng]-DUQA.srt
Skipping file: Zombieland.[2009].DVDRIP.XVID.[Eng]-DUQA.srt as all values in the 'speaker' column are NA's.
Processing file: Zookeeper.RETAiL.BDRip.srt
Processing file: Zoolander.2001.1080p.Blu-ray.Remux.AVC.DTS-HD.MA.5.1.-.KRaLiMaRKo_en.sdh.srt
Processing file: Zoom.2006.1080p.AMZN.WEB-DL.DDP5.1.srt
Processing file: [60313] Life or Something Like It (2002).srt
Skipping file: [60313] Life or Something Like It (2002).srt as all values in the 'speaker' column are NA's.
Processing file: [60385] Big Trouble (2002).srt
Skipping file: [60385] Big Trouble (2002).srt as all values in the 'speaker' column are NA's.
Processing file: [63135] Big Fat Liar (2002).srt
Skipping file: [63135] Big Fat Liar (2002).srt as all values in the 'speaker' column are NA's.
Processing file: [76943] Bless The Child (2000).srt
Skipping file: [76943] Bless The Child (2000).srt as all values in the 'speaker' column are NA's.
Processing file: [ENG-HI]2.Fast.2.Furious.DVDRiP.XViD-DEiTY.By.GrupoUtopia.(grupoutopia.cjb.net).srt
Skipping file: [ENG-HI]2.Fast.2.Furious.DVDRiP.XViD-DEiTY.By.GrupoUtopia.(grupoutopia.cjb.net).srt as all values in the 'speaker' column are NA's.
Processing file: [English] A Cinderella Story.srt
Processing file: [ENG].The.Life.Of.David.Gale - Hearing.Impared.srt
Skipping file: [ENG].The.Life.Of.David.Gale - Hearing.Impared.srt as all values in the 'speaker' column are NA's.
Processing file: Æon Flux.srt