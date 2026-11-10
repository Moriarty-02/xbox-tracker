import requests
from bs4 import BeautifulSoup
import os
import re

# --- Configuración ---
TOKEN = '9192610529:AAESTlTjCNgAH5M8y5fCKrAwJlOmrBVGQB0'
CHAT_ID = 'TU_CHAT_ID_AQUI' 
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
    try:
        respuesta = requests.get(url, timeout=10)
        if respuesta.status_code == 200:
            for articulo in respuesta.json().get('results', []):
                item_id = str(articulo.get('id'))
                precio = articulo.get('price')
                titulo = articulo.get('title').lower()
                condicion = articulo.get('condition')
                link = articulo.get('permalink')
                
                if precio <= PRECIO_MAX and 'series s' in titulo and 'consola' in titulo:
                    if item_id not in vistos:
                        estado = "Nuevo" if condicion == 'new' else "Seminuevo"
                        enviar_telegram(f"🟡 ¡Mercado Libre!\nXbox Series S ({estado})\nPrecio: ${precio} MXN\nLink: {link}")
                        guardar_visto(item_id)
    except: pass

def rastrear_amazon(vistos):
    url = "https://www.amazon.com.mx/s?k=xbox+series+s+consola"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        respuesta = requests.get(url, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            for art in soup.find_all('div', {'data-component-type': 's-search-result'}):
                titulo_elem = art.find('h2')
                precio_elem = art.find('span', {'class': 'a-price-whole'})
                item_id = str(art.get('data-asin'))
                
                if titulo_elem and precio_elem and item_id:
                    titulo = titulo_elem.text.lower()
                    precio_str = precio_elem.text.replace(',', '').replace('.', '').strip()
                    if precio_str.isdigit():
                        precio = float(precio_str)
                        if precio <= PRECIO_MAX and 'series s' in titulo and 'consola' in titulo:
                            if item_id not in vistos:
                                enviar_telegram(f"🔵 ¡Amazon México!\nXbox Series S\nPrecio: ${precio} MXN\nLink: https://www.amazon.com.mx/dp/{item_id}")
                                guardar_visto(item_id)
    except: pass

def rastrear_elektra(vistos):
    # Usando la API interna de Elektra para saltar bloqueos
    url = "https://www.elektra.mx/api/catalog_system/pub/products/search/xbox%20series%20s"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            for prod in res.json():
                titulo = prod.get('productName', '').lower()
                link = prod.get('link', '')
                item_id = str(prod.get('productId'))
                if 'series s' in titulo and 'consola' in titulo:
                    try:
                        precio = prod['items'][0]['sellers'][0]['commertialOffer']['Price']
                        if precio > 0 and precio <= PRECIO_MAX:
                            if item_id not in vistos:
                                enviar_telegram(f"🔴 ¡Elektra!\nXbox Series S\nPrecio: ${precio} MXN\nLink: {link}")
                                guardar_visto(item_id)
                    except: pass
    except: pass

def rastrear_promodescuentos(vistos):
    # Monitorea Walmart, Aurrera, Coppel, etc. mediante alertas de la comunidad
    url = "https://www.promodescuentos.com/search?q=xbox+series+s"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for art in soup.find_all('article'):
                texto = art.text.lower()
                if 'series s' in texto:
                    # Busca texto en formato de dinero en la publicación
                    precios_encontrados = re.findall(r'\$\s?[\d,]+\.?\d*', art.text)
                    for p in precios_encontrados:
                        precio_limpio = p.replace('$', '').replace(',', '').replace(' ', '').strip()
                        try:
                            precio = float(precio_limpio)
                            # Filtramos precios < 1000 para ignorar audífonos o controles en la misma publicación
                            if precio > 1000 and precio <= PRECIO_MAX:
                                link_elem = art.find('a')
                                if link_elem:
                                    link = link_elem.get('href', '')
                                    if link.startswith('/'):
                                        link = "https://www.promodescuentos.com" + link
                                    item_id = "promo_" + link.split('-')[-1]
                                    if item_id not in vistos:
                                        enviar_telegram(f"🔥 ¡Alerta Multi-Tienda (Bodega Aurrera, Walmart, etc)!\nXbox Series S\nPrecio aprox: ${precio} MXN\nRevisa aquí: {link}")
                                        guardar_visto(item_id)
                                        break
                        except: pass
    except: pass

if __name__ == '__main__':
    historial_vistos = cargar_vistos()
    rastrear_mercadolibre(historial_vistos)
    rastrear_amazon(historial_vistos)
    rastrear_elektra(historial_vistos)
    rastrear_promodescuentos(historial_vistos)
