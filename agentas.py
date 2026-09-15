import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# Jūsų nurodytos tiesioginės nuorodos
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
            # Saugiai užkoduojame nuorodą, kad API jos nesugadintų
            encoded_url = quote(url, safe='')
            scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={encoded_url}&render_js=false"
            
            response = requests.get(scrapingbee_url, timeout=30)
            print(f"-> {parduotuve} HTTP statusas: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                pavadinimas = None
                kaina = None
                
                if parduotuve == "Senukai":
                    # Paieška Senukų puslapyje
                    pav_el = soup.select_one("h1")
                    # Ieškom elementų, kurie dažniausiai talpina kainą Senukuose
                    kain_el = soup.select_one(".price, span[data-price], .catalog-price")
                    if pav_el: pavadinimas = pavadin_el.get_text(strip=True)
                    if kain_el: kaina = kain_el.get_text(strip=True)
                    
                else:  # Ermitazas
                    # Paieška Ermitažo puslapyje
                    pav_el = soup.select_one("h1")
                    # Ermitažo kainos blokai
                    kain_el = soup.select_one(".price, .product-price, span[data-price]")
                    if pav_el: pavadinimas = pav_el.get_text(strip=True)
                    if kain_el: kaina = kain_el.get_text(strip=True)
                
                if pavadinimas and kaina:
                    rezultatai.append({
                        "Parduotuve": parduotuve,
                        "Prekė": pavadinimas,
                        "Kaina": kaina
                    })
                    print(f"-> Sėkmė! Rasta: {pavadinimas} | Kaina: {kaina}")
                else:
                    print(f"-> Puslapis gautas, bet nepavyko tiksliai rasti kainos ar pavadinimo elementų.")
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
