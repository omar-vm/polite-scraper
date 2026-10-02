import requests
from pathlib import Path
import time
from datetime import datetime, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup


# ==========================================
# Configuración de rutas
# ==========================================
CACHE_DIR = Path("cache")
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"

BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"
HEADERS = {
        "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/omar-vm/polite-scraper)"
}


# ==========================================
# Lógica de Red y Caché
# ==========================================
def fetch_html(url: str, filename: str) -> str:
    """Descarga el HTML de forma educada o lo lee desde la caché local."""
    cache_file = CACHE_DIR / filename
    
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")
        
    print(f"FETCH: Descargando {url}...")
    try:
        time.sleep(0.5)
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            cache_file.write_text(html, encoding="utf-8")
            return html
        else:
            print(f"Error HTTP {response.status_code} al descargar {url}")
            return ""
            
    except requests.RequestException as e:
        print(f"Error de red en {url}: {e}")
        return ""


# ==========================================
# Lógica de Extracción (Scraping)
# ==========================================
def discover_books() -> dict[str, str]:
    """Retorna un diccionario {url_del_libro: url_de_origen}."""
    current_url = BASE_URL
    pages_visited = 0
    discovered_urls = {} # Usamos dict para guardar la URL de procedencia y evitar duplicados
    
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
                # Guardamos de qué página de catálogo provino este libro
                discovered_urls[absolute_url] = current_url
        
        next_button = soup.select_one("li.next a")
        if next_button and 'href' in next_button.attrs:
            current_url = urljoin(current_url, next_button['href'])
        else:
            current_url = None
            
    return discovered_urls

def extract_book_details(book_url: str, source_page: str) -> dict:
    """Extrae los 8 campos requeridos de la página de detalle de un libro."""
    book_id = book_url.split('/')[-2]
    filename = f"book-{book_id}.html"
    
    html = fetch_html(book_url, filename)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    
    product_main = soup.select_one("div.product_main")
    
    title = product_main.select_one("h1").text if product_main and product_main.select_one("h1") else None
    price_text = product_main.select_one("p.price_color").text if product_main else None
    
    availability_tag = product_main.select_one("p.availability") if product_main else None
    availability_text = availability_tag.text.strip() if availability_tag else None
    
    rating_tag = product_main.select_one("p.star-rating") if product_main else None
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

if __name__ == "__main__":
    books_dict = discover_books()
    
    raw_records = []
    print("\nIniciando extracción de detalles...")
    
    for book_url, source_page in books_dict.items():
        record = extract_book_details(book_url, source_page)
        if record:
            raw_records.append(record)

    print("\n--- EJEMPLO DE REGISTRO CRUDO ---")
    import json
    print(json.dumps(raw_records[0], indent=2, ensure_ascii=False))
    
    print(f"\ndetail_pages = {len(raw_records)}")