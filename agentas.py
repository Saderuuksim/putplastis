import requests
from bs4 import BeautifulSoup

# Nurodome konkrečias paieškos nuorodas EPS 100 putplasčiui Senukuose ir Ermitaže
parduotuves = {
    "Senukai": "https://www.senukai.lt/s/eps-100/4090",
    "Ermitazas": "https://www.ermitazas.lt/p/s/eps-100"
}

def patikrinti_putplascio_kainas():
    # Naudojame naršyklės simuliacijos antraštę, kad svetainės neatmestų užklausos kaip roboto
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    rezultatai = []
    
    for parduotuve, url in parduotuves.items():
        print(f"Jungiamasi prie {parduotuve}...")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Pastaba: el. parduotuvės dažnai atnaujina savo HTML struktūras.
                # Žemiau pateikti bendriniai elementų ieškojimo būdai pagal tipines el. parduotuvių korteles.
                
                if parduotuve == "Senukai":
                    prekes = soup.select("div.catalog-grid-item, div.js-product-grid-item")
                else:  # Ermitazas
                    prekes = soup.select("div.product-card, div.catalog-item")
                
                if not prekes:
                    print(f"-> Nerasta prekių kortelių {parduotuve}. Gali būti, kad puslapis naudoja JavaScript arba pasikeitė kodas.")
                    continue

                skaicius = 0
                for preke in prekes:
                    # Bandome ištraukti pavadinimą ir kainą pagal dažniausiai pasitaikančius selektorius
                    pavadinimo_el = preke.select_one("span.item-title, a.product-title, .title")
                    kainos_el = preke.select_one("span.price, .price-number, span[data-price]")
                    
                    if pavadinimo_el and kainos_el:
                        pavadinimas = pavadinimo_el.get_text(strip=True)
                        kaina = kainos_el.get_text(strip=True)
                        
                        # Filtruojame pagal jūsų nurodytus kriterijus (EPS 100)
                        if "eps 100" in pavadinimas.lower():
                            rezultatai.append({
                                "Parduotuve": parduotuve,
                                "Prekė": pavadinimas,
                                "Kaina": kaina
                            })
                            skaicius += 1
                
                print(f"-> {parduotuve}: rasta tinkančių prekių: {skaicius}")
            else:
                print(f"-> Klaida pasiekiant {parduotuve}: HTTP kodas {response.status_code}")
                
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
        print("Per šį patikrinimą nepavyko automatiškai ištraukti kainų (tikėtina dėl el. parduotuvių apsaugų arba pasikeitusios HTML struktūros).")
