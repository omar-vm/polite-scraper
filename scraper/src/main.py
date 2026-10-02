import requests
from pathlib import Path
import time
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
def discover_books() -> set[str]:
    """Navega por las primeras 3 páginas del catálogo y extrae las URLs absolutas."""
    current_url = BASE_URL
    pages_visited = 0
    discovered_urls = set()  # Usar 'set' elimina duplicados automáticamente
    
    while current_url and pages_visited < 3:
        pages_visited += 1
        filename = f"catalogue-page-{pages_visited}.html"
        
        # Obtener HTML
        html = fetch_html(current_url, filename)
        if not html:
            break
            
        # Parsear con BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Extraer enlaces de los libros (están dentro de 'article.product_pod h3 a')
        for article in soup.select("article.product_pod"):
            link_tag = article.select_one("h3 a")
            if link_tag and 'href' in link_tag.attrs:
                relative_url = link_tag['href']
                # urljoin fusiona inteligentemente la ruta base con la relativa
                absolute_url = urljoin(current_url, relative_url)
                discovered_urls.add(absolute_url)
        
        # Buscar el enlace a la siguiente página ('li.next a')
        next_button = soup.select_one("li.next a")
        if next_button and 'href' in next_button.attrs:
            next_relative = next_button['href']
            current_url = urljoin(current_url, next_relative)
        else:
            current_url = None  # No hay más páginas
            
    # Resultados del Checkpoint
    print(f"catalogue_pages = {pages_visited}")
    print(f"discovered = {len(discovered_urls)}")
    print(f"unique_urls = {len(discovered_urls)}")
    
    return discovered_urls


if __name__ == "__main__":
    book_urls = discover_books()