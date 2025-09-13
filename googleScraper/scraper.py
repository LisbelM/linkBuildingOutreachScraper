import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

API_KEY = ""
keyword = ""

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}"

def get_search_results(query, num_results=20):
    """Fetch search results using SerpAPI."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "num": num_results,
        "api_key": API_KEY,
    }
    response = requests.get(url, params=params)
    data = response.json()
    links = [res["link"] for res in data.get("organic_results", [])]
    return links

def extract_emails_from_url(url):
    """Scrape a page and extract emails."""
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        emails = re.findall(EMAIL_REGEX, soup.get_text())
        return set(emails), soup
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return set(), None

def find_contact_page(base_url, soup):
    """Look for a contact page link inside the page."""
    if not soup:
        return None

    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "contact" in href:
            return urljoin(base_url, a["href"])
    return None

def main():
    links = get_search_results(keyword)
    print(f"Found {len(links)} links for keyword '{keyword}'")

    all_emails = {}
    for link in links:
        print(f"\nScraping: {link}")
        site_emails, soup = extract_emails_from_url(link)

        # Look for a contact page
        contact_url = find_contact_page(link, soup)
        if contact_url:
            print(f"  Found contact page: {contact_url}")
            contact_emails, _ = extract_emails_from_url(contact_url)
            site_emails.update(contact_emails)

        if site_emails:
            all_emails[link] = list(site_emails)

    # Print results
    for site, emails in all_emails.items():
        print(f"\n{site}")
        for email in emails:
            print(f"  {email}")

if __name__ == "__main__":
    main()
