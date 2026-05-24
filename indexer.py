"""
Inverted Index Builder
    Takes the raw course text, then cleans it by
    removing common words, and builds an Inverted
    Index to make searches quick.
"""
# Import necessary libraries
import json
from collections import defaultdict

# Common words that do not add real meaning to a search query.
# Helps us keep our search results relevant and save space.
STOPWORDS = {"a","the","is","are","was","were","and","for",
            "or","but","in","on","at","to","of","with",
            "this","that","it","as","an","be","by","from"
            }

# Load the raw scraped dat from scrape_ocw.py
with open("index.json", "r", encoding = "utf-8") as f:
    data = json.load(f)

# Maps a specific word to a list of all documents that
# contain it
inverted_index = defaultdict(list)

# Loop through each course doc 
for i, doc in enumerate(data):
    # Convert everything to lowercase and split into individual words
    words = doc["content"].lower().split()
    
    # Clean the words
    words = [w for w in words if w not in STOPWORDS and len(w)>2]
    
    # Use a set to ensure UNIWUE words per document
    for word in set(words):
        # Append the current ID to index
        inverted_index[word].append(i)

# Save index to disk
with open("inverted_index.json","w", encoding = "utf-8") as f:
    json.dump(inverted_index,f, ensure_ascii= False)

print(f"Index built! {len(inverted_index)} unique terms indexed")
