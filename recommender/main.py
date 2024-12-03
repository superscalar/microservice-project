import os
import sys
from flask import Flask, session, send_from_directory, request
app = Flask(__name__)

import history
import recommender

print("Movie Recommender service v0.1")

print("Initializing history module...")
history.history_init()
print("Done initializing history module")

print("Initializing recommender module...")
recommender.recommender_init()
print("Done initializing recommender module")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@app.get("/getRecommendation/<user_id>")
def getRecommendation(user_id):
    print(f'[DEBUG] Recommending a movie for {user_id}')
    movie = recommender.getRecommendationForUser(user_id)
    return movie, {'Content-Type': 'application/json'}