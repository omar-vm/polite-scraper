# The Polite Scraper (FlyRank Internship - A9)

## Target Classification

- **Site:** Books to Scrape (books.toscrape.com)
- **Why:** It is a public practice sandbox explicitly built so people can practice scraping.
- **Scope:** The first 3 catalogue pages only.
- **Data Collected:** Book details (title, price, availability, rating, and description).
- **Robots.txt:** No robots file found (404 Not Found). A missing file is not permission, it is just a missing file.

I will not reuse this code on another site without checking its rules and terms first.

## Installation & Execution

This scraper is built in **Python** using `requests`, `BeautifulSoup4`, and `pydantic`.

To run it locally:

1. Install dependencies: `pip install requests beautifulsoup4 pydantic`
2. Run the script: `python src/main.py`

## Politeness Rules Followed

- **User-Agent:** Identifies this specific scraper and links to this repository.
- **Delay:** Enforces a mandatory 0.5-second wait between real network requests.
- **Timeout:** Set to 10 seconds to avoid hanging on unresponsive servers.
- **Cache:** Saves all fetched HTML pages locally to `cache/` to prevent hammering the server during development and subsequent runs.

## Record Schema

Each valid record in `output/books.json` follows this strict Pydantic schema:

- `title` (string)
- `product_url` (absolute URL)
- `price_text` (raw string)
- `price_gbp` (float)
- `availability_text` (string)
- `rating_text` (string, optional)
- `description` (string, optional)
- `source_page` (absolute URL of the catalogue page)
- `fetched_at` (ISO 8601 UTC timestamp)

## Architecture Notes

- **Limitation:** The script currently extracts data sequentially (synchronously), which is safe and polite but slower than asynchronous fetching.
- **No Browser Needed:** This assignment required no headless browser (like Playwright/Puppeteer) because all target data is present in the initial HTML payload sent by the server. Launching a browser would only add unnecessary memory and CPU costs.

## Ethics Note

Web scraping is a powerful tool that must be used responsibly. I commit to:

1. Using an official API whenever one exists.
2. Never bypassing logins, paywalls, or blocks.
3. Collecting only the data strictly necessary for the task.

## Run Report Evidence

Here is the raw output from a successful execution demonstrating the survival of a broken link test:

```json
--- FINAL REPORT ---
{
  "start_time": "2026-10-02T17:42:50.982685+00:00",
  "duration_seconds": 1.61,
  "stats": {
    "pages_fetched": 1,
    "cache_hits": 63,
    "failed_pages": 1,
    "valid_records": 60,
    "invalid_records": 0
  }
}
```
