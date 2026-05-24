"""
BM25 Search Engine
    The search interface. It takes a user query,
    calculates relevance scores using the BM25 algorithm,
    and displays the most relevant courses.
"""

# Import necessary libraries
import json
from rank_bm25 import BM25Okapi

# Load our structured course data
with open ("index.json","r", encoding = "utf-8") as f:
    data = json.load(f)

# Prepare the corpus
# BM25 requires to read every doc as a list of
# tokens to analyze word patterns
corpus = [doc["content"].lower().split() for doc in data]

# Initialize BM25 Okapi model 
bm25 = BM25Okapi(corpus)

# Get search input from user
query = input("Search:")

# Tokenize the query
tokens = query.lower().split()

# Calculate the relevance score for every single doc
# against the search tokens
scores = bm25.get_scores(tokens)

# Rank the docs by score
top_indexes = sorted(range(len(scores)),
                    key = lambda i: scores[i],
                    reverse = True)[:5]     

# Display best matching results
print("\n--- TOP SEARCH RESULTS ---")
for i in top_indexes:
    print(f"\n Title: {data[i]['title']}")
    print(f" ⭐BM25 Score: {scores[i]:.4f}")
    print(f"\n 🔗Link {data[i]['source']}")
    print(f"\n 📝Preview: {data[i]['content'][:300]}...")
