import os
import requests
from bs4 import BeautifulSoup

# Jūsų nurodytos tiesioginės nurodos
parduotuves = {
    "Senukai": "https://www.senukai.lt/p/putplastis-bewi-eps100-100-cm-x-100-cm-x-10-cm/e69k?mtd=searchPage&src=lupasearch",
    "Ermitazas": "https://www.ermitazas.lt/p/polistireninio-putplascio-plokste-termoporas-eps100-100-x-1000-x-1000-mm-crd62v6v"
}

def patikrinti_putplascio_kainas():
    # Pasiimame ScrapingBee API raktą iš GitHub saugyklos
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    
    if not api_key:
        print("Klaida: nerastas SCRAPINGBEE_API_KEY raktas nustatymuose!")
        return []

    rezultatai = []
    
    for parduotuve, url in parduotuves.items():
        print(f"Jungiamasi prie {parduotuve} per ScrapingBee...")
        try:
            # Sukuriame užklausą per ScrapingBee API su JavaScript palaikymu
            scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={url}&render_js=false"
            
            response = requests.get(scrapingbee_url, timeout=30)
            print(f"-> {parduotuve} HTTP statusas: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Priklausomai nuo parduotuvės, ištraukiame pavadinimą ir kainą
                if parduotuve == "Senukai":
                    pavadinimo_el = soup.select_one("h1.product-details-title, h1")
                    kainos_el = soup.select_one("span.price, div.price span, span[data-price]")
                else:  # Ermitazas
                    pavadinimo_el = soup.select_one("h1.product-title, h1")
                    kainos_el = soup.select_one("span.price, div.price, span[data-price]")
                
                if pavadinimo_el and kainos_el:
                    pavadinimas = pavadinimo_el.get_text(strip=True)
                    kaina = kainos_el.get_text(strip=True)
                    
                    rezultatai.append({
                        "Parduotuve": parduotuve,
                        "Prekė": pavadinimas,
                        "Kaina": kaina
                    })
                    print(f"-> Sėkmė! Rasta: {pavadinimas} | Kaina: {kaina}")
                else:
                    print(f"-> Puslapis gautas, bet nepavyko tiksliai rasti kainos elementų struktūros.")
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
