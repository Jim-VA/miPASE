"""
MIT OCW Hybrid Crawler
    This crawler combines a curated list of high-quality Computer Science and Math courses with an automated sitemap-based crawler for broad discovery.
"""
# Libraries
import json
import time
import httpx
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

# Set robots.txt
rp = RobotFileParser()
rp.set_url("https://ocw.mit.edu/robots.txt")
rp.read()

def can_crawl(url):
    return rp.can_fetch("*", url)

# Curated list, classified by academic area
seed_urls = [
    # Algorithms & Data Structures
    "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/",
    "https://ocw.mit.edu/courses/6-046j-design-and-analysis-of-algorithms-spring-2015/",
    "https://ocw.mit.edu/courses/6-851-advanced-data-structures-spring-2012/",
    "https://ocw.mit.edu/courses/6-854j-advanced-algorithms-fall-2005/",
    "https://ocw.mit.edu/courses/6-045j-automata-computability-and-complexity-spring-2011/",

    # AI & Machine Learning
    "https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/",
    "https://ocw.mit.edu/courses/6-867-machine-learning-fall-2006/",
    "https://ocw.mit.edu/courses/6-864-advanced-natural-language-processing-fall-2005/",
    "https://ocw.mit.edu/courses/6-438-algorithms-for-inference-fall-2014/",
    "https://ocw.mit.edu/courses/6-036-introduction-to-machine-learning-fall-2020/",

    # Mathematics & Theory
    "https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-fall-2010/",
    "https://ocw.mit.edu/courses/18-404j-theory-of-computation-fall-2020/",
    "https://ocw.mit.edu/courses/18-065-matrix-methods-in-data-analysis-signal-processing-and-machine-learning-spring-2018/",
    "https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/",
    "https://ocw.mit.edu/courses/18-650-statistics-for-applications-fall-2016/",

    # Software Engineering & Programming
    "https://ocw.mit.edu/courses/6-001-structure-and-interpretation-of-computer-programs-spring-2005/",
    "https://ocw.mit.edu/courses/6-005-software-construction-spring-2016/",
    "https://ocw.mit.edu/courses/6-821-programming-languages-fall-2002/",
    "https://ocw.mit.edu/courses/6-189-a-gentle-introduction-to-programming-using-python-january-iap-2008/",
    "https://ocw.mit.edu/courses/6-005-elements-of-software-construction-fall-2008/",
    "https://ocw.mit.edu/courses/6-170-software-studio-spring-2013/",

    # Systems & Networks
    "https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/",
    "https://ocw.mit.edu/courses/6-033-computer-system-engineering-spring-2018/",
    "https://ocw.mit.edu/courses/6-829-computer-networks-fall-2002/",
    "https://ocw.mit.edu/courses/6-826-principles-of-computer-systems-spring-2002/",
    "https://ocw.mit.edu/courses/1-00-introduction-to-computers-and-engineering-problem-solving-spring-2012/",
] 

# Sitemap crawler, discovers courses
def discover_urls(max_courses=15):
    sitemap_url = "https://ocw.mit.edu/sitemap.xml"
    try:
        response = httpx.get(sitemap_url, timeout=10)
        soup = BeautifulSoup(response.text, "xml")
        
        cs_sitemaps = []    # 6- courses
        math_sitemaps = []  # 18- courses
        
        for loc in soup.find_all("loc"):
            url = loc.text
            if "/courses/6-" in url:
                cs_sitemaps.append(url)
            elif "/courses/18-" in url:
                math_sitemaps.append(url)

        # Take half from each
        half = max_courses // 2
        selected = cs_sitemaps[:half] + math_sitemaps[:half]
        
        # Extract main page from each sitemap
        urls = []
        for sitemap in selected:
            try:
                r = httpx.get(sitemap, timeout=10)
                s = BeautifulSoup(r.text, "xml")
                for loc in s.find_all("loc"):
                    url = loc.text
                    if url.count("/") == 5 and not url.endswith(".xml"):
                        urls.append(url)
                        break
            except:
                continue
        
        return urls
    except Exception as e:
        print(f"Sitemap error: {e}")
        return []

# One page scraper
def scrape(url):
    if not can_crawl(url):
        print(f"Blocked: {url}")
        return None
    try:
        # HTTP petition to get the HTML from the course webpage
        response = httpx.get(url, timeout=10)
        soup = BeautifulSoup(response.text,"html.parser")
        # Main title extraction
        title = soup.find("h1")
        title = title.get_text(separator = " ", strip = True)
        # All content extraction, normalizing spaces
        content = soup.get_text(separator=" ", strip = True)
        return {"source":url, "title": title, "content": content}
    # For network failures, parsing errors or
    # changes in the page's structure
    except Exception as e:
        print(f"{url}: {e}")
        return None

# Main (execution)
if __name__ == "__main__":
    # STEP 1 - Crawler
    print("Discovering URLs from sitemap...")
    crawled_urls = discover_urls(max_courses=25)
    print(f"Found {len(crawled_urls)} crawled URLs")

    # STEP 2 - Merge with curated list (no duplicates)
    all_urls = list(set(crawled_urls + seed_urls))
    print(f"Total: {len(crawled_urls)} crawled + {len(seed_urls)} seeded = {len(all_urls)} unique\n")

    # STEP 3 - Scraper
    results = []
    for i, url in enumerate(all_urls):
        print(f"Scraping ({i+1}/{len(all_urls)}): {url}")
        data = scrape(url)
        if data:
            results.append(data)
        time.sleep(1)
    
    # STEP 4 - Save
    with open("data/index.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {len(results)} courses → data/index.json")
