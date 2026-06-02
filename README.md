# Web Information Retieval project

MiPASE is a simple search engine to look for free high-quality academic courses in STEM areas.


## Project Structure

```
jarvis/
├── data/
│   ├── index.json            # Scraped course data
│   └── inverted_index.json   # BM25 inverted index
├── static/
│   ├── css/
│   │   └── style.css
│   └── images/
│       └── persona.svg
├── templates/
│   └── index.html            # Frontend UI
├── app.py                    # Flask API + RAG (Groq)
├── crawler.py                # Hybrid sitemap + seed crawler
├── indexer.py                # Inverted index builder
├── search.py                 # BM25 search (CLI)
├── mcp_server.py             # MCP tool: search_courses()
├── test_mcp.py               # MCP client test
├── requirements.txt
├── Procfile                  # Render deployment
└── .env.example              # Environment variables template
```
