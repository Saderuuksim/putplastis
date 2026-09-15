import requests
from bs4 import BeautifulSoup

# Nurodome konkrečias paieškos nuorodas EPS 100 putplasčiui Senukuose ir Ermitaže
parduotuves = {
    "Senukai": "https://www.senukai.lt/p/putplastis-bewi-eps100-100-cm-x-100-cm-x-10-cm/e69k?mtd=searchPage&src=lupasearch",
    "Ermitazas": "https://www.ermitazas.lt/p/polistireninio-putplascio-plokste-termoporas-eps100-100-x-1000-x-1000-mm-crd62v6v"
}

def patikrinti_putplascio_kainas():
    # Naudojame išsamesnes naršyklės antraštes (Headers), kad sistema mus matytų kaip tikrą naudotoją
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "lt-LT,lt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    rezultatai = []
    
    # Naudojame 'requests.Session()', kas padeda išlaikyti naršyklės sesijos „atmintį“
    session = requests.Session()
    
    for parduotuve, url in parduotuves.items():
        print(f"Jungiamasi prie {parduotuve}...")
        try:
            response = session.get(url, headers=headers, timeout=15)
            
            print(f"-> {parduotuve} HTTP statusas: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if parduotuve == "Senukai":
                    prekes = soup.select("div.catalog-grid-item, div.js-product-grid-item, div.product-card")
                else:  # Ermitazas
                    prekes = soup.select("div.product-card, div.catalog-item")
                
                if not prekes:
                    print(f"-> Nerasta prekių kortelių {parduotuve} (gali būti apsauga arba pasikeitusi struktūra).")
                    continue

                skaicius = 0
                for preke in prekes:
                    pavadinimo_el = preke.select_one("span.item-title, a.product-title, .title, h3")
                    kainos_el = preke.select_one("span.price, .price-number, span[data-price], .price")
                    
                    if pavadinimo_el and kainos_el:
                        pavadinimas = pavadinimo_el.get_text(strip=True)
                        kaina = kainos_el.get_text(strip=True)
                        
                        if "eps 100" in pavadinimas.lower():
                            rezultatai.append({
                                "Parduotuve": parduotuve,
                                "Prekė": pavadinimas,
                                "Kaina": kaina
                            })
                            skaicius += 1
                
                print(f"-> {parduotuve}: rasta tinkančių prekių: {skaicius}")
            else:
                print(f"-> Prieiga apribota arba klaida (HTTP kodas {response.status_code})")
                
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
        print("Per šį patikrinimą nepavyko automatiškai ištraukti kainų (reikės papildomų nustatymų).")
