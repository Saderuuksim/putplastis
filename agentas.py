import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

parduotuves = {
    "Senukai": "https://www.senukai.lt/p/putplastis-bewi-eps100-100-cm-x-100-cm-x-10-cm/e69k?mtd=searchPage&src=lupasearch",
    "Ermitazas": "https://www.ermitazas.lt/p/polistireninio-putplascio-plokste-termoporas-EPS100-100-x-1000-x-1000-mm-crd62v6v",
    "Lemora": "https://lemora.lt/izoliacija-sandarinimas/silumos-garso-izoliacija/putu-plokstes/68-putplastis-termoporas-eps-100-nefrezuotas",
    "ViskasNamams": "https://viskasnamams.lt/p/polistirolas-eps100-100-x-1000-x-1000-mm-1-210",
    "MokiVezi": "https://mokivezi.lt/1065467-polistireninis-putplastis-etna-eps-100-matmenys-100-x-1000-x-1200-mm-1pak-0-72-m3"
}

def patikrinti_putplascio_kainas():
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    
    if not api_key:
        print("Klaida: nerastas SCRAPINGBEE_API_KEY raktas nustatymuose!")
        return []

    rezultatai = []
    
    for parduotuve, url in parduotuves.items():
        print(f"Jungiamasi prie {parduotuve}...")
        try:
            encoded_url = quote(url, safe='')
            
            if parduotuve in ["Senukai", "MokiVezi"]:
                scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={encoded_url}&render_js=true"
            else:
                scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={encoded_url}&render_js=false"
            
            response = requests.get(scrapingbee_url, timeout=45)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                pavadinimas = None
                kaina = None
                
                h1_el = soup.select_one("h1")
                if h1_el:
                    pavadinimas = h1_el.get_text(strip=True)
                
                # Tikslus kainos traukimas pagal parduotuves
                if parduotuve == "Senukai":
                    for el in soup.find_all(['span', 'div', 'p']):
                        t = el.get_text(strip=True)
                        if ('€' in t or 'EUR' in t) and len(t) < 20 and any(c.isdigit() for c in t):
                            kaina = t
                            break
                elif parduotuve == "Ermitazas":
                    for el in soup.find_all(['span', 'div', 'strong']):
                        t = el.get_text(strip=True)
                        if len(t) in [4, 5, 6] and t.replace('.', '').replace(',', '').isdigit() and int(t) > 10:
                            if '.' not in t and ',' not in t:
                                kaina = f"{t[:-2]},{t[-2:]} €"
                            else:
                                kaina = t + " €"
                            break
                elif parduotuve == "Lemora":
                    # Lemoros kainos blokas
                    for el in soup.select("div, span"):
                        t = el.get_text(strip=True)
                        if '€' in t and ('pak' in t.lower() or len(t) < 10) and any(c.isdigit() for c in t):
                            kaina = t
                            break
                elif parduotuve == "ViskasNamams":
                    for el in soup.select("div, span"):
                        t = el.get_text(strip=True)
                        if '€' in t and '/' in t and any(c.isdigit() for c in t) and len(t) < 25:
                            kaina = t
                            break
                elif parduotuve == "MokiVezi":
                    for el in soup.select("div, span"):
                        t = el.get_text(strip=True)
                        if '€' in t and 'pak' in t.lower() and any(c.isdigit() for c in t) and len(t) < 25:
                            kaina = t
                            break

                if pavadinimas and kaina:
                    rezultatai.append({
                        "Parduotuve": parduotuve,
                        "Prekė": pavadinimas[:40] + "..." if len(pavadinimas) > 40 else pavadinimas,
                        "Kaina": kaina
                    })
                    print(f"-> {parduotuve}: Rasta kaina {kaina}")
                else:
                    print(f"-> {parduotuve}: Nepavyko rasti kainos.")
            else:
                print(f"-> {parduotuve}: HTTP klaida {response.status_code}")
                
        except Exception as e:
            print(f"-> {parduotuve}: Klaida - {e}")

    return rezultatai

if __name__ == "__main__":
    gauti_duomenys = patikrinti_putplascio_kainas()
    print("\n" + "="*80)
    print(f"{'PARDUOTUVĖ':<15} | {'PREKĖ':<45} | {'KAINA':<15}")
    print("="*80)
    if gauti_duomenys:
        for r in gauti_duomenys:
            print(f"{r['Parduotuve']:<15} | {r['Prekė']:<45} | {r['Kaina']:<15}")
    else:
        print("Kainų nerasta.")
    print("="*80)
