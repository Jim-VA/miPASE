"""
MIT OCW Syllabus Web Scraper
    Extracts the title and text content from the
    selected curses from MIT OpenCourseWare for
    their later indexation and search via BM25.
"""


# Import necessary libraries
import json
import httpx
from bs4 import BeautifulSoup

# URLs to be scraped, classified by academic area
urls = [
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

# Final container for the structured docs
data = []

print("Data extraction is starting...\n")

for url in urls:
    try:
        # HTTP petition to get the HTML from the course webpage
        response = httpx.get(url)
        soup = BeautifulSoup(response.text,"html.parser")
        
        # Main title extraction 
        title = soup.find("h1").get_text(strip = True)
        
        # All content extraction, normalizing spaces
        body = soup.get_text(separator = " ", strip = True)

        #Doc structure key:value
        data.append({"source": url, 
                    "title": title,
                    "content": body
                    })

        print(f"{title} saved succesfully!")
    except Exception as e:
        # For network failures, parsing errors or
        #  changes in the page's structure
        print(f"Error on {url}: {e}")

with open("index.json","w",encoding = "utf-8") as f:
    json.dump(data,f,ensure_ascii = False, indent = 2)

print (f"\n {len(data)} courses saved!")