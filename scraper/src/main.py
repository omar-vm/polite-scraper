import json
import time
from urllib.parse import urljoin
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import requests
from pathlib import Path
from pydantic import BaseModel, HttpUrl, ValidationError
from typing import Optional

# ==========================================
# Configuration and Constants
# ==========================================
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"
HEADERS = {
    # Replace with your actual repository URL
    "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/omar-vm/polite-scraper)"
}

# 1. Object to track run metrics (Stage 5)
STATS = {
    "pages_fetched": 0,
    "cache_hits": 0,
    "failed_pages": 0,
    "valid_records": 0,
    "invalid_records": 0
}

# ==========================================
# Validation Schema (Stage 4)
# ==========================================
class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: Optional[str] = None
    description: Optional[str] = None
    source_page: HttpUrl
    fetched_at: datetime

# ==========================================
# Network and Cache Logic with Retries (Stage 5)
# ==========================================
def fetch_html(url: str, filename: str) -> str:
    cache_file = CACHE_DIR / filename
    
    # Read from local cache if available
    if cache_file.exists():
        STATS["cache_hits"] += 1
        return cache_file.read_text(encoding="utf-8")
        
    print(f"FETCH: Downloading {url}...")
    
    # 2. Retry logic: Maximum 2 attempts (1 initial + 1 retry)
    for attempt in range(2):
        try:
            time.sleep(0.5)
            STATS["pages_fetched"] += 1
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                cache_file.write_text(html, encoding="utf-8")
                return html
                
            # Permanent errors: Do not retry (e.g., 404 Not Found, 403 Forbidden)
            elif response.status_code in (403, 404):
                print(f"Permanent error {response.status_code} on {url}. Skipping...")
                STATS["failed_pages"] += 1
                return ""
                
            # Temporary server errors: Retry
            elif response.status_code >= 500:
                print(f"Server error {response.status_code} on {url}. Retrying...")
                time.sleep(2) # Brief backoff before retrying
                continue
                
        except requests.Timeout:
            print(f"Timeout on {url}. Retrying...")
            time.sleep(2)
            continue
            
        except requests.RequestException as e:
            print(f"Critical network error on {url}: {e}")
            STATS["failed_pages"] += 1
            return ""
            
    # If all attempts are exhausted
    STATS["failed_pages"] += 1
    return ""

# ==========================================
# Extraction Logic (Stages 2 and 3)
# ==========================================
def discover_books() -> dict[str, str]:
    current_url = BASE_URL
    pages_visited = 0
    discovered_urls = {} 
    
    while current_url and pages_visited < 3:
        pages_visited += 1
        filename = f"catalogue-page-{pages_visited}.html"
        
        html = fetch_html(current_url, filename)
        if not html:
            break
            
        soup = BeautifulSoup(html, "html.parser")
        
        for article in soup.select("article.product_pod"):
            link_tag = article.select_one("h3 a")
            if link_tag and 'href' in link_tag.attrs:
                absolute_url = urljoin(current_url, link_tag['href'])
                discovered_urls[absolute_url] = current_url
        
        next_button = soup.select_one("li.next a")
        if next_button and 'href' in next_button.attrs:
            current_url = urljoin(current_url, next_button['href'])
        else:
            current_url = None
            
    return discovered_urls

def extract_book_details(book_url: str, source_page: str) -> dict:
    book_id = book_url.split('/')[-2] if len(book_url.split('/')) > 2 else "unknown"
    filename = f"book-{book_id}.html"
    
    html = fetch_html(book_url, filename)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.select_one("div.product_main")
    
    if not product_main:
        return {}
        
    title = product_main.select_one("h1").text if product_main.select_one("h1") else None
    price_text = product_main.select_one("p.price_color").text if product_main.select_one("p.price_color") else None
    
    availability_tag = product_main.select_one("p.availability")
    availability_text = availability_tag.text.strip() if availability_tag else None
    
    rating_tag = product_main.select_one("p.star-rating")
    rating_text = rating_tag["class"][1] if rating_tag and len(rating_tag["class"]) > 1 else None

    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.text if description_tag else None

    return {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }

# ==========================================
# Cleaning and Validation Logic (Stage 4)
# ==========================================
def clean_price(price_text: str) -> float:
    if not price_text:
        return 0.0
    # Extract only digits and the decimal point
    clean_text = "".join(c for c in price_text if c.isdigit() or c == '.')
    return float(clean_text) if clean_text else 0.0

def process_and_validate(raw_records: list[dict]) -> tuple[list[dict], list[dict]]:
    unique_books = {} 
    errors = []

    for record in raw_records:
        if not record:
            continue
            
        if record.get("price_text"):
            record["price_gbp"] = clean_price(record["price_text"])
            
        try:
            validated_book = BookRecord(**record)
            url_str = str(validated_book.product_url)
            # Dump objects to JSON-compatible formats
            unique_books[url_str] = validated_book.model_dump(mode='json')
            
        except ValidationError as e:
            errors.append({
                "product_url": record.get("product_url", "Unknown"),
                "error_details": e.errors()
            })
            
    return list(unique_books.values()), errors

# ==========================================
# Main Execution
# ==========================================
if __name__ == "__main__":
    start_time = time.time()
    
    print("Discovering catalogue...")
    books_dict = discover_books()
    
    # 3. POISONED PILL TEST (Stage 5): Injecting a fake URL intentionally
    fake_url = "https://books.toscrape.com/catalogue/fake-book-does-not-exist/index.html"
    books_dict[fake_url] = "https://books.toscrape.com/catalogue/page-1.html"
    print(f"Injected fake URL for testing. Total to process: {len(books_dict)}")
    
    print("\nStarting extraction and validation of details...")
    raw_records = []
    
    for book_url, source_page in books_dict.items():
        record = extract_book_details(book_url, source_page)
        if record:
            raw_records.append(record)

    # Process, clean, and validate
    good_records, error_records = process_and_validate(raw_records)
    
    STATS["valid_records"] = len(good_records)
    STATS["invalid_records"] = len(error_records)
    
    # Save records to disk
    (OUTPUT_DIR / "books.json").write_text(json.dumps(good_records, indent=2, ensure_ascii=False), encoding="utf-8")
    
    if error_records:
        (OUTPUT_DIR / "errors.json").write_text(json.dumps(error_records, indent=2, ensure_ascii=False), encoding="utf-8")
        
    # 4. Generate and save run report
    end_time = time.time()
    run_report = {
        "start_time": datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(),
        "duration_seconds": round(end_time - start_time, 2),
        "stats": STATS
    }
    
    (OUTPUT_DIR / "run-report.json").write_text(json.dumps(run_report, indent=2), encoding="utf-8")
    
    # Checkpoint Stage 5
    print(f"\n--- FINAL REPORT ---")
    print(json.dumps(run_report, indent=2))