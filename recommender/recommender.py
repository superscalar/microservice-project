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

    # There are duplicate titles in the dataset. E.g. "47 Ronin" appears twice
    # It makes sense. What can't be a duplicate is the ID, not the title.
    # But that means I may be grabbing the wrong title.
    # Since I have the ID, it's better to use get_recommendations_for_ID
    if type(idx) == type(pd.Series()):
        print(f"[DEBUG] Found {len(idx)} titles when there should've been 1 (movie index {idx[0]})")
        idx = idx[0]

    # Compute the cosine similarities on the go instead of precomputing it
    # (which causes a crash in Docker due to memory limitations)
    # Later, this can be cached to make it even more efficient
    sim_scores = list(enumerate(cosine_similarity(count_matrix, count_matrix[idx])))
    sim_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Since the list of similarity scores is now sorted, the comparison of this movie to itself is the first element,
    # which we don't want --> slice it off
    sim_scores = sim_scores[1:n+1]
    
    movie_indices = [i[0] for i in sim_scores]
    scores = [i[1] for i in sim_scores]

    recommended_movies = movies.iloc[movie_indices].copy()
    recommended_movies['sim_score'] = scores

    return recommended_movies

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_recommendations_for_ID(movieID, n=10):
    movie = movies.loc[movies.id == movieID]
    try:
        idx = movie.index.values[0]
    except IndexError:
        # Invalid ID, therefore there's no index to be found
        return json.dumps({})

    # Compute the cosine similarities on the go instead of precomputing it
    # (which causes a crash in Docker due to memory limitations)
    # Later, this can be cached to make it even more efficient
    sim_scores = list(enumerate(cosine_similarity(count_matrix, count_matrix[idx])))
    sim_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Since the list of similarity scores is now sorted, the comparison of this movie to itself is the first element,
    # which we don't want --> slice it off
    sim_scores = sim_scores[1:n+1]
    
    movie_indices = [i[0] for i in sim_scores]
    scores = [i[1] for i in sim_scores]

    recommended_movies = movies.iloc[movie_indices].copy()
    recommended_movies['sim_score'] = scores

    return recommended_movies

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~+

N_RECOMMENDATIONS = 5

import sys

alreadySeenMovies = defaultdict(list) # indexed by user ID - holds the list of movies that have already been seen

# indexed by movie ID - holds a DataFrame of N_RECOMMENDATIONS recommendations. Serves as a recommendation cache
# This doesn't have anything to do with the user ID because it's independent of each user.
movieRecommendations = {}

def getRecommendationForUser(userID):
    # userHistory being a list of HistoryRecord dataclasses which is mutable from here
    userHistory = history.getHistoryForUser(userID)
    print("f[DEBUG] User {userID} history == ", userHistory)

    if (len(userHistory) == 0):
        print(f"[DEBUG] The user {userID} hasn't shown interest in any movie: recommend them anything")
        return movies.sample(1).to_json(orient='records')

    IDs = [record.movieID for record in userHistory]    
    titleForID = lambda movieID: movies.loc[movies["id"] == movieID]["title"].values[0]
    id_title_pairs = zip(IDs, map(titleForID, IDs))

    recommendations = []
    for movieID, title in id_title_pairs:

        # We've seen it already
        if movieID in movieRecommendations:
            recommendations.append(movieRecommendations[movieID])
        else:
            recommendationsForThisMovie = get_recommendations_for_ID(movieID, N_RECOMMENDATIONS)
            recommendations.append(recommendationsForThisMovie)
            movieRecommendations[movieID] = recommendationsForThisMovie.copy()

    # print(f"\n\n\n\n [DEBUG] Recommendations computed from {IDs} =>")
    # for dfs in recommendations:
    #     print(dfs.head())
    # print("\n\n")

    all_recommendations = pd.concat(recommendations) # there's duplicates, but I just can't find a way to remove them
    all_recommendations = all_recommendations.drop_duplicates(subset='id')
    random_recommended_movie = all_recommendations.sample(1)

    return random_recommended_movie.to_json(orient='records')