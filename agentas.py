import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

parduotuves = {
    "Senukai": "https://www.senukai.lt/p/putplastis-bewi-eps100-100-cm-x-100-cm-x-10-cm/e69k?mtd=searchPage&src=lupasearch",
    "Ermitazas": "https://www.ermitazas.lt/p/polistireninio-putplascio-plokste-termoporas-EPS100-100-x-1000-x-1000-mm-crd62v6v"
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
            
            if parduotuve == "Senukai":
                scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={encoded_url}&render_js=true"
            else:
                scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={encoded_url}&render_js=false"
            
            response = requests.get(scrapingbee_url, timeout=45)
            print(f"-> {parduotuve} HTTP statusas: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                pavadinimas = None
                kaina = None
                
                h1_el = soup.select_one("h1")
                if h1_el:
                    pavadinimas = h1_el.get_text(strip=True)
                
                if parduotuve == "Senukai":
                    for el in soup.find_all(['span', 'div', 'p']):
                        tekstas = el.get_text(strip=True)
                        if ('€' in tekstas or 'EUR' in tekstas) and len(tekstas) < 20 and any(c.isdigit() for c in tekstas):
                            kaina = tekstas
                            break
                else:
                    # Ermitažui: ieškome kainos konteinerio arba suapvalintų kainos dalių
                    # Dažnai e-parduotuvėse kaina pasiekiama per bendrą kainos bloką
                    price_container = soup.select_one(".price, [class*='price'], [class*='kaina']")
                    if price_container:
                        kaina = price_container.get_text(strip=True)
                    
                    # Jei per klasę nepavyko, ieškome pagal elementus, kurie savo viduje turi skaičius be raidžių (gryna kaina)
                    if not kaina:
                        for el in soup.find_all(['span', 'div', 'strong']):
                            tekstas = el.get_text(strip=True)
                            # Ermitažo lojalumo kaina nuotraukoje atrodo kaip dideli skaičiai (pvz., 5699 arba 56.99)
                            if len(tekstas) in [4, 5, 6] and tekstas.replace('.', '').replace(',', '').isdigit():
                                if '.' in tekstas or ',' in tekstas or int(tekstas) > 10:
                                    kaina = tekstas + " €"
                                    break

                if pavadinimas and kaina:
                    rezultatai.append({
                        "Parduotuve": parduotuve,
                        "Prekė": pavadinimas,
                        "Kaina": kaina
                    })
                    print(f"-> Sėkmė! Rasta: {pavadinimas} | Kaina: {kaina}")
                else:
                    print(f"-> Puslapis gautas, bet nepavyko išrinkti kainos.")
                    if pavadinimas:
                        print(f"   Pavadinimas: {pavadinimas}")
            else:
                print(f"-> Parduotuvė pasiekta su klaidos kodu: {response.status_code}")
                
        except Exception as e:
            print(f"-> Įvyko klaida jungiantis prie {parduotuve}: {e}")

    return rezultatai

if __name__ == "__main__":
    gauti_duomenys = patikrinti_putplascio_kainas()
    print("\n--- REZULTATAI ---")
    if gauti_duomenys:
        for r in gauti_duomenys:
            print(f"[{r['Parduotuve']}] {r['Prekė']} | Kaina: {r['Kaina']}")
    else:
        print("Per šį patikrinimą kainų nepavyko ištraukti.")
