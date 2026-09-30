from http.server import BaseHTTPRequestHandler
import cloudscraper
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Mapeo de minerales (Hierro y Carbón) con símbolos en Trading Economics
        minerales_target = {
            'SCO1:COM': 'Hierro',
            'COAL:COM': 'Carbón'
        }
        resultados = {}
        
        try:
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            
            url = "https://tradingeconomics.com/commodities"
            res = scraper.get(url, timeout=10)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Búsqueda por símbolo exacto
                for symbol, nombre in minerales_target.items():
                    try:
                        fila = soup.find('tr', {'data-symbol': symbol})
                        
                        # Si no encuentra el símbolo directo de Carbón, busca por nombre de enlace en el HTML
                        if not fila and nombre == 'Carbón':
                            fila = soup.find('a', href=lambda h: h and '/commodity/coal' in h)
                            if fila:
                                fila = fila.find_parent('tr')

                        if not fila and nombre == 'Hierro':
                            fila = soup.find('a', href=lambda h: h and '/commodity/iron-ore' in h)
                            if fila:
                                fila = fila.find_parent('tr')

                        if fila:
                            precio_raw = fila.find('td', id='p')
                            resultados[nombre] = precio_raw.text.strip() if precio_raw else "N/A"
                        else:
                            resultados[nombre] = "No encontrado"
                    except Exception:
                        resultados[nombre] = "Error al procesar"
                
                payload = {
                    "datos": resultados,
                    "status": "success"
                }
                status_code = 200
            else:
                payload = {"error": f"Error del sitio origen: {res.status_code}"}
                status_code = 502

        except Exception as e:
            payload = {"error": str(e)}
            status_code = 500

        # Respuesta JSON para Vercel
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))
        return
