"""
MCP Server
    Exposes MIT OCW course search as an MCP tool.
    That way any LLM can call it automatically.
"""

# Libraries
import json          
import asyncio       # MCP uses async
from rank_bm25 import BM25Okapi  
from groq import Groq              # LLM for reranking
from dotenv import load_dotenv     
import os

# MCP-specific imports:
# Server = the actual server object (like Flask's app = Flask())
# stdio_server = communication channel via terminal input/output
# types = MCP data types (Tool, TextContent, etc.)
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv()  # Load GROQ_API_KEY from .env file

# ── SETUP ────────────────────────────────────────────────────
# Load our scraped course data — same as app.py
# This runs ONCE when the server starts, not on every search
with open("data/index.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Pre-build the BM25 index in memory
# Like building a library catalog once so searches are instant
corpus = [doc["content"].lower().split() for doc in data]
bm25 = BM25Okapi(corpus)

# Groq client for RAG reranking
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Create the MCP server — give it a name
# Like app = Flask(__name__) but for MCP
server = Server("mipase-search")

# ── TOOL DEFINITION ──────────────────────────────────────────
# This tells any LLM: "here's what I can do and how to call me"
# Like a menu at a restaurant — the LLM reads it and decides
# when and how to order from you
@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="search_courses",  # LLM calls this by name
            description="Search MIT OpenCourseWare courses by topic. Returns top 3 relevant courses with explanations.",
            # inputSchema tells the LLM what parameters to send
            # Like a form: "fill in 'query' to search"
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Topic to search (e.g. 'algorithms', 'machine learning')"
                    }
                },
                "required": ["query"]  # query is mandatory
            }
        )
    ]

# ── TOOL EXECUTION ────────────────────────────────────────────
# This runs every time the LLM calls search_courses(query)
# Like a waiter taking the order to the kitchen
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    
    # Safety check — only handle our tool
    if name != "search_courses":
        raise ValueError(f"Unknown tool: {name}")
    
    query = arguments.get("query", "")
    
    # ── STEP 1: BM25 Retrieval ────────────────────────────────
    # Same logic as app.py — keyword search over indexed courses
    # Returns top 5 candidates by relevance score
    tokens = query.lower().split()
    scores = bm25.get_scores(tokens)
    top5 = sorted(range(len(scores)),
                  key=lambda i: scores[i],
                  reverse=True)[:5]
    
    candidates = [{
        "title": data[i]["title"],
        "source": data[i]["source"],
        "snippet": data[i]["content"][:300],
        "score": round(scores[i], 4)
    } for i in top5]

    # ── STEP 2: RAG Reranking ─────────────────────────────────
    # Ask Groq's LLM to pick the TOP 3 from the 5 candidates
    # and explain WHY each is relevant
    # This adds semantic understanding beyond keyword matching
    try:
        prompt = f"""You are an academic search assistant.
A student searched for: "{query}"

Here are 5 candidate courses:
{json.dumps([{"title": c["title"], "snippet": c["snippet"][:200]} for c in candidates], indent=2)}

Select the TOP 3 most relevant courses.
Respond ONLY in this JSON format:
[
  {{"title": "Course Title", "reason": "Why relevant"}},
  {{"title": "Course Title", "reason": "Why relevant"}},
  {{"title": "Course Title", "reason": "Why relevant"}}
]"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3  # Low temp = more consistent, less creative
        )

        # Extract text from Groq's response
        raw = response.choices[0].message.content.strip()
        
        # Sometimes LLMs wrap JSON in ```json ... ``` — strip that
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        reranked = json.loads(raw.strip())

        # Match LLM's chosen titles back to our full candidate data
        # Like connecting a name on a list to a full profile
        results = []
        seen = set()  # Prevent duplicate results
        for item in reranked:
            for c in candidates:
                if (item["title"].lower() in c["title"].lower() or
                    c["title"].lower() in item["title"].lower()):
                    if c["title"] not in seen:
                        seen.add(c["title"])
                        results.append({
                            "title": c["title"],
                            "source": c["source"],
                            "reason": item.get("reason", "")
                        })
                    break

        # If RAG matching failed, fall back to raw BM25 top 3
        output = results if results else candidates[:3]

    except Exception as e:
        # If Groq fails for any reason, return BM25 results directly
        # Graceful degradation — better a simple answer than no answer
        print(f"RAG error: {e}")
        output = candidates[:3]

    # ── RETURN ────────────────────────────────────────────────
    # MCP requires returning a list of Content objects
    # TextContent = plain text/JSON that the LLM can read
    # Think of it as the server's "response" to the LLM's "request"
    return [types.TextContent(
        type="text",
        text=json.dumps(output, ensure_ascii=False, indent=2)
    )]

# ── RUN ───────────────────────────────────────────────────────
# stdio_server = communicate via terminal (stdin/stdout)
# This is the standard MCP transport — works with any MCP client
# Like starting Flask with app.run() but for MCP
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream,
                        server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
