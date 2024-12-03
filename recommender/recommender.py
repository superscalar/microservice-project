import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from rapidfuzz.process import extractOne

import datetime as dt
from collections import defaultdict
from random import choices

import history
import pickle

def recommender_init():
    global cosine_sim, indices, titles, movies
    global count_matrix

    movies = pd.read_csv("movies_clean.csv")
    print("[RECOMMENDER] Debug: CountVectorizer fit_transform")
    count = CountVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0.0, stop_words='english')
    count_matrix = count.fit_transform(movies['soup'])
    print("[RECOMMENDER] Debug: CountVectorizer fit_transform done")
    indices = pd.Series(movies.index, index=movies['title'])
    titles = movies['title']

def get_recommendations(title, n=10):
    try:
        idx = indices[title]
    except KeyError:
        # If title isn't found, then find the nearest title with a fuzzy matching algorithm
        # We only care about one result, so a list of matches isn't wanted here.
        # Rapidfuzz's extractOne is perfect for this
        fuzzyMatchTitle = extractOne(query = title, choices = movies['title'], score_cutoff=90)
        idx = indices[ fuzzyMatchTitle[0] ]

    # Compute the cosine similarities on the go instead of precomputing it
    # (which causes a crash in Docker due to memory limitations)
    # Later, this can be cached to make it even more efficient
    sim_scores = list(enumerate(cosine_similarity(count_matrix[idx], count_matrix)))

    sim_scores.sort(key=lambda x: x[1].any(), reverse=True)
    
    # Since the list of similarity scores is now sorted, the comparison of this movie to itself is the first element,
    # which we don't want --> slice it off
    sim_scores = sim_scores[1:n+1]
    
    movie_indices = [i[0] for i in sim_scores]
    scores = [i[1] for i in sim_scores]

    recommended_movie = movies.iloc[movie_indices].copy()
    recommended_movie['sim_score'] = scores

    return recommended_movie

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~+

N_RECOMMENDATIONS = 5

def getRecommendationForUser(userID):
    # userHistory being a list of HistoryRecord dataclasses which is mutable from here
    userHistory = history.getHistoryForUser(userID)

    if (len(userHistory) == 0):
        # the user hasn't shown interest in any movie -> recommend them anything
        return movies.sample(1).to_json(orient='records')

    # Only process new records.
    newRecords = filter(lambda r: not r.seen, userHistory)
    for record in newRecords: record.seen = True
    IDs = [record.movieID for record in newRecords]

    titleForID = lambda movieID: movies.loc[movies["id"] == movieID]["title"].values[0]
    id_title_zip = zip(IDs, map(titleForID, IDs))
    recommendations = [ get_recommendations(title, N_RECOMMENDATIONS) for movieID, title in id_title_zip ]
    all_recommendations = pd.concat(recommendations) # there's duplicates, but I just can't find a way to remove them
    random_recommended_movie = all_recommendations.sample(1)
    return random_recommended_movie.to_json(orient='records')