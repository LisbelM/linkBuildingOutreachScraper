import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from collections import deque

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}"
ALLOWED_KEYWORDS = ["links", "partners", "contact", "friends"]

def extract_emails(text):
    return set(re.findall(EMAIL_REGEX, text))

def get_links(html, base_url, depth):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a['href'])
        if not href.startswith("http"):
            continue

        # Only allow deeper traversal (depth >= 1) on "links" or "partners" pages
        path = href.lower()
        if depth == 0:  
            # From the seed page, allow all links
            links.add(href)
        else:
            # Only follow if URL contains one of the allowed keywords
            if any(keyword in path for keyword in ALLOWED_KEYWORDS):
                links.add(href)
    return links

def crawl(start_url, max_depth=2, max_pages=50):
    visited = set()
    emails = set()
    queue = deque([(start_url, 0)])
    
    while queue and len(visited) < max_pages:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue

        try:
            response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            if "text/html" not in response.headers.get("Content-Type", ""):
                continue
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        visited.add(url)
        html = response.text

        # Extract emails
        found_emails = extract_emails(html)
        if found_emails:
            print(f"Found {found_emails} on {url}")
            emails.update(found_emails)

        # Extract and filter links based on depth
        links = get_links(html, url, depth)
        for link in links:
            if link not in visited:
                queue.append((link, depth + 1))

    return emails

if __name__ == "__main__":
    start = "https://arsenalcore.com/arsenal-blogs/"
    all_emails = crawl(start, max_depth=2, max_pages=1000)
    print("\nCollected Emails:", all_emails)