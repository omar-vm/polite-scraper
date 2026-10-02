import requests
from pathlib import Path

# 1. Configuración de rutas
CACHE_DIR = Path("cache")
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"
URL = "https://books.toscrape.com/catalogue/page-1.html"

def fetch_page_1():
    # Asegurarnos de que la carpeta cache/ exista
    CACHE_DIR.mkdir(exist_ok=True)

    # 2. LÓGICA DE CACHÉ
    if CACHE_FILE.exists():
        html = CACHE_FILE.read_text(encoding="utf-8")
        print(f"CACHE HIT: Leído desde caché local ({len(html)} bytes).")
        return html

    print("FETCH: Descargando la página del servidor...")
    
    headers = {
        "User-Agent": "FlyRankInternship-A9/1.0 (+https://github.com/omar-vm/polite-scraper)"
    }

    try:
        # Petición con límite de 10 segundos
        response = requests.get(URL, headers=headers, timeout=10)
        
        # Detener la ejecución si el servidor nos rechaza (ej. 404, 500)
        if response.status_code != 200:
            print(f"Error: El servidor devolvió el código {response.status_code}")
            return None
            
        html = response.text
        
        # 4. Guardamos el HTML en disco para futuras ejecuciones
        CACHE_FILE.write_text(html, encoding="utf-8")
        print(f"FETCH: Guardado exitosamente ({len(html)} bytes).")
        
        return html
        
    except requests.Timeout:
        print("Error: La petición tardó demasiado tiempo (Timeout).")
        return None

if __name__ == "__main__":
    html_content = fetch_page_1()