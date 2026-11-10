import requests
from bs4 import BeautifulSoup
import os

# --- Configuración ---
TOKEN = '9192610529:AAESTlTjCNgAH5M8y5fCKrAwJlOmrBVGQB0'
CHAT_ID = 'R8343436298'
PRECIO_MAX = 5000.0
ARCHIVO_VISTOS = 'xbox_vistos.txt'

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': mensaje})

def cargar_vistos():
    if os.path.exists(ARCHIVO_VISTOS):
        with open(ARCHIVO_VISTOS, 'r') as f:
            return set(f.read().splitlines())
    return set()

def guardar_visto(item_id):
    with open(ARCHIVO_VISTOS, 'a') as f:
        f.write(f"{item_id}\n")

def rastrear_mercadolibre(vistos):
    url = "https://api.mercadolibre.com/sites/MLM/search?q=xbox%20series%20s%20consola"
    respuesta = requests.get(url)
    
    if respuesta.status_code == 200:
        for articulo in respuesta.json().get('results', []):
            item_id = articulo.get('id')
            precio = articulo.get('price')
            titulo = articulo.get('title').lower()
            condicion = articulo.get('condition')
            link = articulo.get('permalink')
            
            if precio <= PRECIO_MAX and 'series s' in titulo and 'consola' in titulo:
                if item_id not in vistos:
                    estado = "Nuevo" if condicion == 'new' else "Seminuevo"
                    mensaje = f"🟡 ¡Mercado Libre!\nXbox Series S ({estado})\nPrecio: ${precio} MXN\nLink: {link}"
                    enviar_telegram(mensaje)
                    guardar_visto(item_id)

def rastrear_amazon(vistos):
    url = "https://www.amazon.com.mx/s?k=xbox+series+s+consola"
    # Headers para simular un navegador real y evitar bloqueos
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9"
    }
    
    try:
        respuesta = requests.get(url, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            articulos = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for art in articulos:
                titulo_elem = art.find('h2')
                precio_elem = art.find('span', {'class': 'a-price-whole'})
                item_id = art.get('data-asin')
                
                if titulo_elem and precio_elem and item_id:
                    titulo = titulo_elem.text.lower()
                    precio_str = precio_elem.text.replace(',', '').replace('.', '').strip()
                    
                    if precio_str.isdigit():
                        precio = float(precio_str)
                        if precio <= PRECIO_MAX and 'series s' in titulo and 'consola' in titulo:
                            if item_id not in vistos:
                                link = "https://www.amazon.com.mx/dp/" + item_id
                                mensaje = f"🔵 ¡Amazon México!\nXbox Series S\nPrecio: ${precio} MXN\nLink: {link}"
                                enviar_telegram(mensaje)
                                guardar_visto(item_id)
    except Exception:
        pass # Ignora errores de conexión si Amazon bloquea la IP temporalmente

if __name__ == '__main__':
    historial_vistos = cargar_vistos()
    rastrear_mercadolibre(historial_vistos)
    rastrear_amazon(historial_vistos)
