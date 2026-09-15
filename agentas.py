import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

parduotuves = {
    "Senukai": "https://www.senukai.lt/p/putplastis-bewi-eps100-100-cm-x-100-cm-x-10-cm/e69k?mtd=searchPage&src=lupasearch",
    "Ermitazas": "https://www.ermitazas.lt/p/polistireninio-putplascio-plokste-termoporas-EPS100-100-x-1000-x-1000-mm-crd62v6v",
    "ViskasNamams": "https://viskasnamams.lt/p/polistirolas-eps100-100-x-1000-x-1000-mm-1-210",
    "MokiVezi": "https://mokivezi.lt/1065467-polistireninis-putplastis-etna-eps-100-matmenys-100-x-1000-x-1200-mm-1pak-0-72-m3"
}

def patikrinti_putplascio_kainas():
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    if not api_key:
        print("Klaida: nerastas SCRAPINGBEE_API_KEY!")
        return []

    rezultatai = []
    
    for parduotuve, url in parduotuves.items():
        print(f"Jungiamasi prie {parduotuve}...")
        try:
            encoded_url = quote(url, safe='')
            scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={encoded_url}&render_js=false"
            
            response = requests.get(scrapingbee_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                pavadinimas, kaina = None, None
                
                h1_el = soup.select_one("h1")
                if h1_el:
                    pavadinimas = h1_el.get_text(strip=True)
                
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
                elif parduotuve == "ViskasNamams":
                    for el in soup.find_all(['span', 'div', 'strong']):
                        t = el.get_text(strip=True)
                        if '€' in t and '/' in t and any(c.isdigit() for c in t) and len(t) < 25:
                            kaina = t
                            break
                elif parduotuve == "MokiVezi":
                    for el in soup.find_all(['span', 'div', 'strong', 'b']):
                        t = el.get_text(strip=True)
                        if ('€' in t or 'pak' in t.lower()) and len(t) < 15 and any(c.isdigit() for c in t):
                            skaitmenys = "".join([c for c in t if c.isdigit()])
                            if len(skaitmenys) == 4:
                                kaina = f"{skaitmenys[:-2]},{skaitmenys[-2:]} € / pak."
                                break
                            elif '€' in t:
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
                print(f"-> {parduotuve}: Praleista (statusas {response.status_code})")
        except Exception as e:
            print(f"-> {parduotuve}: Klaida - {e}")

    return rezultatai

def siusti_el_pasta(rezultatai):
    sender_email = os.getenv("GMAIL_USER")
    sender_password = os.getenv("GMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        print("Klaida: Nerasti el. pašto kintamieji (GMAIL_USER arba GMAIL_PASSWORD).")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = sender_email
    msg['Subject'] = "🏗️ Rytinė putplasčio kainų apžvalga"

    body = "Štai šiandienos rasti kainų rezultatai:\n\n"
    body += f"{'PARDUOTUVĖ':<15} | {'PREKĖ':<45} | {'KAINA':<15}\n"
    body += "-" * 80 + "\n"
    
    for r in rezultatai:
        body += f"{r['Parduotuve']:<15} | {r['Prekė']:<45} | {r['Kaina']:<15}\n"
        
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, sender_email, msg.as_string())
        server.quit()
        print("El. laiškas sėkmingai išsiųstas į Gmail!")
    except Exception as e:
        print(f"Nepavyko išsiųsti el. pašto: {e}")

if __name__ == "__main__":
    gauti_duomenys = patikrinti_putplascio_kainas()
    print("\n" + "="*80)
    print(f"{'PARDUOTUVĖ':<15} | {'PREKĖ':<45} | {'KAINA':<15}")
    print("="*80)
    if gauti_duomenys:
        for r in gauti_duomenys:
            print(f"{r['Parduotuve']:<15} | {r['Prekė']:<45} | {r['Kaina']:<15}")
        print("="*80)
        # Siunčiame el. laišką
        siusti_el_pasta(gauti_duomenys)
    else:
        print("Kainų nerasta.")
        print("="*80)
