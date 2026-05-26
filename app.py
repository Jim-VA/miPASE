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
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize the Flask application
app = Flask(__name__)

# Load the structured course dataset from our data directory
with open("data/index.json", "r",encoding="utf-8") as f:
    data = json.load(f)

# Pre-tokenize the entire corpus
corpus = [doc["content"].lower().split() for doc in data]
bm25 = BM25Okapi(corpus)

# Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
    import re
    clean = re.sub(r'[^a-zA-Z\s]', '', query)
    words = [w for w in clean.strip().split() if len(w) > 2]
    vowels = set('aeiouAEIOU')
    all_gibberish = all(
        not any(c in vowels for c in w) 
        for w in words
    ) if words else True

    if all_gibberish and len(query) > 3:
        return jsonify({
            "warning": "That doesn't look like a valid search.",
            "suggestions": ["algorithms", "AI", "linear algebra"],
            "results": [],
            "no_exact": False
        })
    
    # BM25 Retrieval
    tokens = query.lower().split() # Tokenize query
    scores = bm25.get_scores(tokens) # Calculate BM25 relevance
    top5 = sorted(range(len(scores)), # Get top 5 docs
                key = lambda i: scores[i],
                reverse = True)[:5]
    
    # Case 3: Stopwords
    STOPWORDS = {"is","a","the","an","are","and","or","to","in","on","for","because"}
    query_words = [w for w in tokens if w not in STOPWORDS]
    if not query_words:
        return jsonify({
            "warning":"Too generic! Please try something more specific.",
            "suggestions":["mathematics","computer science","programming"],
            "results":[],
            "no_exact": False
        }) 
    
    # List of dictionary results to send back to frontend
    candidates = [{"title":data[i]["title"],
                "source":data[i]["source"],
                "snippet": data[i]["content"][:300],
                "score": round(scores[i], 4)
                } for i in top5]
    
    # RAG Reranking
    try:
        prompt = f"""You are an academic search assistant.
        A student searched for:"{query}"
        
        Here are 5 candidate courses:
        {json.dumps([{"title": c["title"], "snippet": c["snippet"][:200]} for c in candidates], indent=2)}
        Select the TOP 3 most relevant courses for this quer.
        Consider semantic meaning, not just exact keywords.
        If the query is irrelevant to all courses, say so.
        
        Respond ONLY in this JSON format, no extra text:
        
        [
        {{"title": "Course Title", "reason": "One sentence why this is relevant"}},
        {{"title": "Course Title", "reason": "One sentence why this is relevant"}},
        {{"title": "Course Title", "reason": "One sentence why this is relevant"}}
        ]"""


        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        raw = response.choices[0].message.content.strip()

        # Clean markdown fences if present
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        reranked = json.loads(raw.strip())

        # Match back to full candidate data
        results = []
        for item in reranked:
            matched = None
            for c in candidates:
                if (item["title"].lower() in c["title"].lower() or 
                    c["title"].lower() in item["title"].lower()):
                    matched = c
                    break
            if matched:
                results.append({
                        "title": matched["title"],
                        "source": matched["source"],
                        "snippet": matched["snippet"][:300],
                        "reason": item.get("reason", ""),
                        "bm25_score": matched["score"]
                    })


        # If no matches found fallback to BM25
        if not results:
            return jsonify(candidates[:3])

        return jsonify(results)

    except Exception as e:
        print(f"RAG error: {e}")
        print(f"Candidates sample:{candidates[0]}")
        # Fallback to BM25 top 3 if Groq fails
        return jsonify(candidates[:3])

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3000, debug=True)