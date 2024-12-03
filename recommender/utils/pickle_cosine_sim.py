# Computing the cosine similarity of every movie against every other movie led to too much memory usage: it was the cartesian product of 23539 elements
# That means 554084521 1x23539 float64 matrices. This made the docker container crash even after increasing its memory limits.
# To solve this, I wanted to trade memory for disk space.
# The idea here was to pickle the cosine_sim result from computing the cosine similarity of Count Vectorizer's result.
# This resulted in a 4 Gb file, which could be mapped as a volume to the docker container. But it crashed when loading the pickled file...
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from rapidfuzz.process import extractOne

import pickle

movies = pd.read_csv("../movies_clean.csv")

print("[RECOMMENDER] Debug: CountVectorizer fit_transform")
count = CountVectorizer(analyzer='word', ngram_range=(1, 2), min_df=0.0, stop_words='english')
count_matrix = count.fit_transform(movies['soup'])
print("[RECOMMENDER] Debug: CountVectorizer fit_transform done")

print("[RECOMMENDER] Debug: Cosine sim")
cosine_sim = cosine_similarity(count_matrix, count_matrix)
print("[RECOMMENDER] Debug: Cosine sim done")

print("Pickling...")
with open("pickled_cosine_sim", "wb") as pickled_cosine_sim:
    pickle.dump(cosine_sim, pickled_cosine_sim, pickle.HIGHEST_PROTOCOL)
print("Done pickling")