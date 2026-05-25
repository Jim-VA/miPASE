"""
Flask Web Backend API
    Turns the BM25 search engine into a web server.
    It handles incoming browser requests, runs the 
    search algorithm, and returns the top 5 results
    as structured JSON dara for the frontend web 
    interface.
"""

# Import necessary libraries
import os

import json

from flask import Flask, request, jsonify, render_template
from rank_bm25 import BM25Okapi

# Initialize the Flask application
app = Flask(__name__)

# Load the structured course dataset from our data directory
with open("data/index.json", "r",encoding="utf-8") as f:
    data = json.load(f)

# Pre-tokenize the entire corpus
corpus = [doc["content"].lower().split() for doc in data]
bm25 = BM25Okapi(corpus)

# Flask Routes act like waiters --> they listen for
# specific orders from the user and respond accordingly

@app.route("/")
def home():
    # Serves the main user interface.
    return render_template("index.html") 

@app.route("/search")
def search():
    # Search API endpoint
    query = request.args.get("q","") # Grab query from URL
    
    # FOOLPROOOFING
    # Case 1: Empty query
    if not query or len(query.strip()) <2:
        return jsonify({
            "warning": "Please enter a search term!",
            "suggestions": ["algorithms", "machine learning", "calculus"]
        })
    
    # Case 2: Gibberish (no vowels or random chars)
    vowels = set ('aiueoAIUEO')
    if len(query) > 3 and not any (c in vowels for c in query):
        return jsonify({
            "warning":"Hmm, that doesn't look like a valid search.",
            "suggestions":["AI","linear algebra","algorithms"]
        })
    
    # BM25 Search
    tokens = query.lower().split() # Tokenize query
    scores = bm25.get_scores(tokens) # Calculate BM25 relevance
    top = sorted(range(len(scores)), # Get top 5 docs
                key = lambda i: scores[i],
                reverse = True)[:5]
    
    # List of dictionary results to send back to frontend
    candidates = [{"title":data[i]["title"],
                "source":data[i]["source"],
                "snippet": data[i]["content"][:300],
                "score": round(scores[i], 4)
                } for i in top]
    
    # Case 3: All scores are zero
    max_score = max(scores) if scores.any() else 0
    if max_score == 0 and len(query) > 6:
        return jsonify({
            "warning": f" No exact matches for '{query}'.",
            "suggestions": ["algorithms", "machine learning","calculus"],
            "results": candidates[:3]
        })
    
    return jsonify(candidates) # Convert Python listo to native JSON format


if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host = "0.0.0.0", port = port)