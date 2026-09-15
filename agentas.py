import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

parduotuves = {
    "Senukai": "https://www.senukai.lt/p/putplastis-bewi-eps100-100-cm-x-100-cm-x-10-cm/e69k?mtd=searchPage&src=lupasearch",
    "Ermitazas": "https://www.ermitazas.lt/p/polistireninio-putplascio-plokste-termoporas-eps100-100-x-1000-x-1000-mm-crd62v6v"
}

def patikrinti_putplascio_kainas():
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    
    if not api_key:
        print("Klaida: nerastas SCRAPINGBEE_API_KEY raktas nustatymuose!")
        return []

    rezultatai = []
    
    for parduotuve, url in parduotuves.items():
        print(f"Jungiamasi prie {parduotuve} per ScrapingBee...")
        try:
            encoded_url = quote(url, safe='')
            # render_js=true leidžia naršyklei pilnai užkrauti puslapio JavaScript elementus (kainas)
            scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={encoded_url}&render_js=true"
            
            response = requests.get(scrapingbee_url, timeout=45)
            print(f"-> {parduotuve} HTTP statusas: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                pavadinimas = None
                kaina = None
                
                # Universalus elementų ieškojimas pagal dažniausiai naudojamas el. parduotuvių klases
                # Ieškome bet kokio h1 elemento (pavadinimui)
                h1_el = soup.select_one("h1")
                if h1_el:
                    pavadinimas = h1_el.get_text(strip=True)
                
                # Ieškome kainos pagal bendresnius atributus arba klases
                # Šiuolaikinės el. parduotuvės kainas dažnai laiko specifinėse klasėse arba meta žymose
                price_el = soup.select_one("[class*='price'], [data-price], .product-price, span.notranslate")
                
                if price_el:
                    kaina = price_el.get_text(strip=True)
                else:
                    # Alternatyva: ieškoti teksto, kuriame yra € ženklas
                    for span in soup.find_all(['span', 'div', 'p']):
                        tekstas = span.get_text(strip=True)
                        if '€' in tekstas and len(tekstas) < 15:
                            kaina = tekstas
                            break

                if pavadinimas and kaina:
                    rezultatai.append({
                        "Parduotuve": parduotuve,
                        "Prekė": pavadinimas,
                        "Kaina": kaina
                    })
                    print(f"-> Sėkmė! Rasta: {pavadinimas} | Kaina: {kaina}")
                else:
                    print(f"-> Puslapis gautas, bet nepavyko automatiškai ištraukti tikslios kainos.")
                    # Jei nepavyko automatiškai, išvedame bent pavadinimą, kad matytume, jog puslapis pasiektas
                    if pavadinimas:
                        print(f"   Rastas pavadinimas: {pavadinimas}")
            else:
                print(f"-> Klaida: ScrapingBee grąžino kodą {response.status_code}")
                
        except Exception as e:
            print(f"-> Įvyko klaida: {e}")

    return rezultatai

if __name__ == "__main__":
    gauti_duomenys = patikrinti_putplascio_kainas()
    print("\n--- REZULTATAI ---")
    if gauti_duomenys:
        for r in gauti_duomenys:
            print(f"[{r['Parduotuve']}] {r['Prekė']} | Kaina: {r['Kaina']}")
    else:
        print("Per šį patikrinimą kainų nepavyko ištraukti.")
