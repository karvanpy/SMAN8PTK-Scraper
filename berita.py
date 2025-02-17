from fastapi import FastAPI, Query
from curl_cffi import requests
from selectolax.parser import HTMLParser
from typing import List, Dict

app = FastAPI(title="Berita Scraper API")

BASE_URL = "https://sman8ptk.sch.id/berita"

def fetch_html(url: str) -> str:
    """Fetches HTML content from a given URL using curl-cffi."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def parse_articles(html: str) -> List[Dict[str, str]]:
    """Parses HTML content and extracts article information."""
    articles_data: List[Dict[str, str]] = []
    if html:
        tree = HTMLParser(html)
        article_elements = tree.css("div.post-content")
        for article_element in article_elements:
            title_element = article_element.css_first("h3 a")
            date_element = article_element.css_first(".post-meta span")
            description_element = article_element.css_first("p")

            article_data = {
                "title": title_element.text(strip=True) if title_element else "No Title",
                "link": title_element.attributes['href'] if title_element else "#",
                "date": date_element.text(strip=True).split('</i>')[-1].strip() if date_element else "No Date",
                "description": description_element.text(strip=True) if description_element else "No Description",
            }
            articles_data.append(article_data)
    return articles_data

@app.get("/scrape-berita", response_model=List[Dict[str, str]], description="Scrape berita from SMAN 8 Pontianak website by page number.")
async def scrape_berita(page: int = Query(1, title="Page number", description="Page number to scrape. Default is 1.", ge=1)):
    """
    Scrape berita articles from SMAN 8 Pontianak website for a specific page.

    - **page**: The page number to scrape (e.g., 1, 2, 3...). Must be a positive integer.
    """
    scrape_url = f"{BASE_URL}?page={page}"
    html_content = fetch_html(scrape_url)
    if html_content:
        articles = parse_articles(html_content)
        return articles
    else:
        return [] # Return empty list if fetching failed

@app.get("/scrape-berita/all", response_model=List[Dict[str, str]], description="Scrape berita from all available pages (Be careful, may take long time).")
async def scrape_berita_all():
    """
    Scrape berita articles from SMAN 8 Pontianak website from all available pages.
    **Warning**: This endpoint may take a long time to complete and might be heavy on the target website. Use with caution.
    """
    all_articles: List[Dict[str, str]] = []
    page_number = 1
    while True:
        scrape_url = f"{BASE_URL}?page={page_number}"
        html_content = fetch_html(scrape_url)
        if not html_content:
            break  # Stop if cannot fetch page, assume no more pages or error
        articles = parse_articles(html_content)
        if not articles: # Stop if no articles on the page, might be end of pagination (or website structure change)
            break
        all_articles.extend(articles)
        page_number += 1
        # Add a small delay to be polite to the website (optional, but recommended)
        # import asyncio
        # await asyncio.sleep(1) # 1 second delay

    return all_articles


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
