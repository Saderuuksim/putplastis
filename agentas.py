import cloudscraper
from bs4 import BeautifulSoup

# Jūsų nurodytos tiesioginės konkrečių prekių nuorodos
parduotuves = {
    "Senukai": "https://www.senukai.lt/p/putplastis-bewi-eps100-100-cm-x-100-cm-x-10-cm/e69k?mtd=searchPage&src=lupasearch",
    "Ermitazas": "https://www.ermitazas.lt/p/polistireninio-putplascio-plokste-termoporas-eps100-100-x-1000-x-1000-mm-crd62v6v"
}

def patikrinti_putplascio_kainas():
    # Sukuriame „cloudscraper“ objektą, kuris apeina Cloudflare apsaugas
    scraper = cloudscraper.create_scraper()
    rezultatai = []
    
    for parduotuve, url in parduotuves.items():
        print(f"Jungiamasi prie {parduotuve}...")
        try:
            response = scraper.get(url, timeout=15)
            print(f"-> {parduotuve} HTTP statusas: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Nustatome elementus pagal parduotuvę (kadangi tai tiesioginiai puslapiai)
                if parduotuve == "Senukai":
                    # Senukų produkto puslapio pavadinimo ir kainos elementai
                    pavadinimo_el = soup.select_one("h1.product-details-title, h1")
                    kainos_el = soup.select_one("span.price, div.price span, span[data-price]")
                else:  # Ermitazas
                    # Ermitažo produkto puslapio pavadinimo ir kainos elementai
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
                    print(f"-> Sekmė! Rasta prekė: {pavadinimas} | Kaina: {kaina}")
                else:
                    print(f"-> Puslapis pasiektas, bet nepavyko tiksliai rasti kainos ar pavadinimo elementų struktūros.")
            else:
                print(f"-> Prieiga apribota (HTTP kodas {response.status_code})")
                
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
        print("Per šį patikrinimą nepavyko ištraukti kainų.")
