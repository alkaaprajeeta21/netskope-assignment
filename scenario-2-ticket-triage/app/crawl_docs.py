import requests
import time
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
import json
import os

BASE_URL = "https://docs.netskope.com"
OUTPUT_DIR = "data/crawled_docs"
MAX_PAGES = 300          # keep it bounded
CRAWL_DELAY = 1.0        # seconds

os.makedirs(OUTPUT_DIR, exist_ok=True)

def is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc.endswith("docs.netskope.com")
        and not any(x in parsed.path for x in ["/login", "/logout", ".pdf"])
    )

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_page(url: str):
    r = requests.get(url, timeout=10)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.title.text.strip() if soup.title else ""

    # Main content heuristic
    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return None

    text = clean_text(main.get_text(" "))

    return {
        "url": url,
        "title": title,
        "text": text,
    }

def crawl():
    visited = set()
    queue = deque([BASE_URL])
    results = []

    while queue and len(results) < MAX_PAGES:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            print(f"Crawling: {url}")
            page = extract_page(url)
            if page and len(page["text"]) > 300:
                results.append(page)

            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                if is_valid_url(link) and link not in visited:
                    queue.append(link)

            time.sleep(CRAWL_DELAY)

        except Exception as e:
            print(f"Failed {url}: {e}")

    out_file = os.path.join(OUTPUT_DIR, "netskope_docs.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved {len(results)} pages to {out_file}")

if __name__ == "__main__":
    crawl()
