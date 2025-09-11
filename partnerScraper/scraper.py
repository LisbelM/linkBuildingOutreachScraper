import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from collections import deque
import csv
import os

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

        path = href.lower()
        if depth == 0:  
            # From the seed page, allow all links
            links.add(href)
        else:
            # Only follow if URL contains one of the allowed keywords
            if any(keyword in path for keyword in ALLOWED_KEYWORDS):
                links.add(href)
    return links

def crawl(start_url, max_depth=2, max_pages=50, output_file="emails.csv"):
    visited = set()
    results = []  # store tuples (url, email)
    queue = deque([(start_url, 0)])
    
    # Load existing results if CSV exists
    existing_results = set()
    if os.path.exists(output_file):
        with open(output_file, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) == 2:
                    existing_results.add((row[0], row[1]))

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
            for email in found_emails:
                if (url, email) not in existing_results:
                    results.append((url, email))
                    existing_results.add((url, email))

        # Extract and filter links based on depth
        links = get_links(html, url, depth)
        for link in links:
            if link not in visited:
                queue.append((link, depth + 1))

    # Write results to CSV (append mode)
    if results:
        file_exists = os.path.exists(output_file)
        with open(output_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["URL", "Email"])  # write header only once
            writer.writerows(results)
        print(f"\n✅ Saved {len(results)} new emails to {output_file}")
    else:
        print("\n⚠️ No new emails found.")

    return results

if __name__ == "__main__":
    start = "https://arsenalcore.com/arsenal-blogs/"
    all_emails = crawl(start, max_depth=5, max_pages=2500, output_file="emails.csv")