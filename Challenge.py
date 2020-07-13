#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json
import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine
import psycopg2
from config import db_password
import time


# In[ ]:


def clean_movie(movie):
    movie = dict(movie) #create a non-destructive copy
    alt_titles = {}
    # combine alternate titles into one list
    for key in ['Also known as','Arabic','Cantonese','Chinese','French',
                'Hangul','Hebrew','Hepburn','Japanese','Literally',
                'Mandarin','McCune-Reischauer','Original title','Polish',
                'Revised Romanization','Romanized','Russian',
                'Simplified','Traditional','Yiddish']:
        if key in movie:
            alt_titles[key] = movie[key]
            movie.pop(key)
    if len(alt_titles) > 0:
        movie['alt_titles'] = alt_titles

    # merge column names
def change_column_name(old_name, new_name):
    if old_name in movie:
        movie[new_name] = movie.pop(old_name)
    change_column_name('Adaptation by', 'Writer(s)')
    change_column_name('Country of origin', 'Country')
    change_column_name('Directed by', 'Director')
    change_column_name('Distributed by', 'Distributor')
    change_column_name('Edited by', 'Editor(s)')
    change_column_name('Length', 'Running time')
    change_column_name('Original release', 'Release date')
    change_column_name('Music by', 'Composer(s)')
    change_column_name('Produced by', 'Producer(s)')
    change_column_name('Producer', 'Producer(s)')
    change_column_name('Productioncompanies ', 'Production company(s)')
    change_column_name('Productioncompany ', 'Production company(s)')
    change_column_name('Released', 'Release Date')
    change_column_name('Release Date', 'Release date')
    change_column_name('Screen story by', 'Writer(s)')
    change_column_name('Screenplay by', 'Writer(s)')
    change_column_name('Story by', 'Writer(s)')
    change_column_name('Theme music composer', 'Composer(s)')
    change_column_name('Written by', 'Writer(s)')

    return movie


# In[ ]:


def parse_dollars(s):
    # if s is not a string, return NaN
    if type(s) != str:
        return np.nan

    # if input is of the form $###.# million
    if re.match(r'\$\s*\d+\.?\d*\s*milli?on', s, flags=re.IGNORECASE):

        # remove dollar sign and " million"
        s = re.sub('\$|\s|[a-zA-Z]','', s)

        # convert to float and multiply by a million
        v = float(s) * 10**6
        # return value
        return v
    # if input is of the form $###.# billion
    elif re.match(r'\$\s*\d+\.?\d*\s*billi?on', s, flags=re.IGNORECASE):

        # remove dollar sign and " billion"
        s = re.sub('\$|\s|[a-zA-Z]','', s)

        # convert to float and multiply by a billion
        v = float(s) * 10**9
        # return value
        return v
    # if input is of the form $###,###,###
    elif re.match(r'\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)', s, flags=re.IGNORECASE):

        # remove dollar sign and commas
        s = re.sub('\$|,','', s)

        # convert to float
        v = float(s)
        # return value
        return v
    # otherwise, return NaN
    else:
        return np.nan


# In[ ]:


def fill_missing_kaggle_data(df, kaggle_column, wiki_column):
    df[kaggle_column] = df.apply(
        lambda row: row[wiki_column] if row[kaggle_column] == 0 else row[kaggle_column]
        , axis=1)
    df.drop(columns=wiki_column, inplace=True)


# In[ ]:
def etl(wiki,kaggle,movie_lens):

    with open(wiki, mode='r') as file:
        wiki_movies_raw = json.load(file)


    # In[ ]:


    kaggle_metadata = pd.read_csv(kaggle, low_memory=False)
    ratings = pd.read_csv(movie_lens)


    # In[ ]:


    wiki_movies_df = pd.DataFrame(wiki_movies_raw)


    # In[ ]:


    ##Directors and IMDB Link. and Number of Episodes
    wiki_movies = [movie for movie in wiki_movies_raw
                    if ('Director' in movie or 'Directed by' in movie)
                    and 'imdb_link' in movie
                    and 'No. of episodes' not in movie]


    # In[ ]:


    clean_movies = [clean_movie(movie) for movie in wiki_movies]
    wiki_movies_df = pd.DataFrame(clean_movies)


    # In[ ]:


    wiki_movies_df['imdb_id'] = wiki_movies_df['imdb_link'].str.extract(r'(tt\d{7})')
    for entry in wiki_movies_df:
        try:
            print(wiki_movies_df)
            wiki_movies_df.drop_duplicates(subset='imdb_id', inplace=True)
        except:
            print('Next entry')
        print(wiki_movies_df)

    # In[ ]:


    ## Execute
    [column for column in wiki_movies_df.columns if wiki_movies_df[column].isnull().sum() < len(wiki_movies_df) * 0.9]


    # In[ ]:


    wiki_columns_to_keep = [column for column in wiki_movies_df.columns if wiki_movies_df[column].isnull().sum() < len(wiki_movies_df) * 0.9]
    wiki_movies_df = wiki_movies_df[wiki_columns_to_keep]


    # In[ ]:


    box_office = wiki_movies_df['Box office'].dropna() 


    # In[ ]:


    box_office = box_office.apply(lambda x: ' '.join(x) if type(x) == list else x)


    # In[ ]:


    box_office = box_office.str.replace(r'\$.*[-—–](?![a-z])', '$', regex=True)


    # In[ ]:


    form_two = r'\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)'
    form_one = r'\$\s*\d+\.?\d*\s*[mb]illi?on'


    # In[ ]:


    wiki_movies_df['box_office'] = box_office.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)


    # In[ ]:


    wiki_movies_df.drop('Box office', axis=1, inplace=True)


    # In[ ]:


    #Budget variable
    budget = wiki_movies_df['Budget'].dropna()


    # In[ ]:


    #Convert listings to strings
    budget = budget.map(lambda x: ' '.join(x) if type(x) == list else x)


    # In[ ]:


    #Remove any values between dollar sign and a hyphen
    budget = budget.str.replace(r'\$.*[-—–](?![a-z])', '$', regex=True)


    # In[ ]:


    matches_form_one = budget.str.contains(form_one, flags=re.IGNORECASE)
    matches_form_two = budget.str.contains(form_two, flags=re.IGNORECASE)


    # In[ ]:


    budget = budget.str.replace(r'\[\d+\]\s*', '')


    # In[ ]:


    ##More Parsing
    wiki_movies_df['budget'] = budget.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)


    # In[ ]:


    #Drop Original Budget Column
    wiki_movies_df.drop('Budget', axis=1, inplace=True)


    # In[ ]:


    #Parse Release Date
    release_date = wiki_movies_df['Release date'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)


    # In[ ]:


    date_form_one = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s[123]\d,\s\d{4}'
    date_form_two = r'\d{4}.[01]\d.[123]\d'
    date_form_three = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}'
    date_form_four = r'\d{4}'
    release_date.str.extract(f'({date_form_one}|{date_form_two}|{date_form_three}|{date_form_four})', flags=re.IGNORECASE)
    wiki_movies_df['release_date'] = pd.to_datetime(release_date.str.extract(f'({date_form_one}|{date_form_two}|{date_form_three}|{date_form_four})')[0], infer_datetime_format=True)


    # In[ ]:


    #Parse Running Time
    running_time = wiki_movies_df['Running time'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)


    # In[ ]:


    running_time_extract = running_time.str.extract(r'(\d+)\s*ho?u?r?s?\s*(\d*)|(\d+)\s*m')


    # In[ ]:


    running_time_extract = running_time_extract.apply(lambda col: pd.to_numeric(col, errors='coerce')).fillna(0)


    # In[ ]:


    wiki_movies_df['running_time'] = running_time_extract.apply(lambda row: row[0]*60 + row[1] if row[2] == 0 else row[2], axis=1)


    # In[ ]:


    wiki_movies_df.drop('Running time', axis=1, inplace=True)


    # In[ ]:


    kaggle_metadata = kaggle_metadata[kaggle_metadata['adult'] == 'False'].drop('adult',axis='columns')


    # In[ ]:


    kaggle_metadata['budget'] = kaggle_metadata['budget'].astype(int)
    kaggle_metadata['id'] = pd.to_numeric(kaggle_metadata['id'], errors='raise')
    kaggle_metadata['popularity'] = pd.to_numeric(kaggle_metadata['popularity'], errors='raise')


    # In[ ]:


    kaggle_metadata['release_date'] = pd.to_datetime(kaggle_metadata['release_date'])


    # In[ ]:


    #Assign to Timestamp Column
    ratings['timestamp'] = pd.to_datetime(ratings['timestamp'], unit='s')


    # In[ ]:


    #Merge Wikipedia and Kaggle Metadata
    movies_df = pd.merge(wiki_movies_df, kaggle_metadata, on='imdb_id', suffixes=['_wiki','_kaggle'])


    # In[ ]:


    movies_df.drop(columns=['title_wiki','release_date_wiki','Language','Production company(s)'], inplace=True)


    # In[ ]:


    fill_missing_kaggle_data(movies_df, 'runtime', 'running_time')
    fill_missing_kaggle_data(movies_df, 'budget_kaggle', 'budget_wiki')
    fill_missing_kaggle_data(movies_df, 'revenue', 'box_office')


    # In[ ]:


    #Reorder Columns
    movies_df = movies_df.loc[:, ['imdb_id','id','title_kaggle','original_title','tagline','belongs_to_collection','url','imdb_link',
                        'runtime','budget_kaggle','revenue','release_date_kaggle','popularity','vote_average','vote_count',
                        'genres','original_language','overview','spoken_languages','Country',
                        'production_companies','production_countries','Distributor',
                        'Producer(s)','Director','Starring','Cinematography','Editor(s)','Writer(s)','Composer(s)','Based on'
                        ]]


    # In[ ]:


    movies_df.rename({'id':'kaggle_id',
                    'title_kaggle':'title',
                    'url':'wikipedia_url',
                    'budget_kaggle':'budget',
                    'release_date_kaggle':'release_date',
                    'Country':'country',
                    'Distributor':'distributor',
                    'Producer(s)':'producers',
                    'Director':'director',
                    'Starring':'starring',
                    'Cinematography':'cinematography',
                    'Editor(s)':'editors',
                    'Writer(s)':'writers',
                    'Composer(s)':'composers',
                    'Based on':'based_on'
                    }, axis='columns', inplace=True)


    # ## Transform and Merge Rating Data

    # In[ ]:


    rating_counts = ratings.groupby(['movieId','rating'], as_index=False).count()                 .rename({'userId':'count'}, axis=1)                 .pivot(index='movieId',columns='rating', values='count')


    # In[ ]:


    rating_counts.columns = ['rating_' + str(col) for col in rating_counts.columns]


    # In[ ]:


    movies_with_ratings_df = pd.merge(movies_df, rating_counts, left_on='kaggle_id', right_index=True, how='left')


    # In[ ]:


    movies_with_ratings_df[rating_counts.columns] = movies_with_ratings_df[rating_counts.columns].fillna(0)


    # In[ ]:


    db_string = f"postgres://postgres:{db_password}@127.0.0.1:5432/movie_data"


    # In[ ]:


    engine = create_engine(db_string)


    # In[ ]:



    movies_df.to_sql(name='movies', con=engine, if_exists='append')


    # In[ ]:


    rows_imported = 0
    # get the start_time from time.time()
    start_time = time.time()
    # for data in pd.read_csv(f'ratings.csv', chunksize=1000000):
    #     print(f'importing rows {rows_imported} to {rows_imported + len(data)}...', end='')
    #     data.to_sql(name='ratings', con=engine, if_exists='append')
    #     rows_imported += len(data)

    #     # add elapsed time to final print out
    #     print(f'Done. {time.time() - start_time} total seconds elapsed')

wiki='wikipedia.movies.json'
kaggle='movies_metadata.csv'
movie_lens='ratings.csv'

etl(wiki, kaggle, movie_lens)

    # In[ ]:




