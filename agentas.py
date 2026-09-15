from datetime import datetime
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests

# ==========================================
# 1. KONFIGŪRACIJA (Slaptieji raktai iš GitHub Secrets)
# ==========================================
SCRAPINGBEE_API_KEY = os.environ.get("SCRAPINGBEE_API_KEY")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO = os.environ.get("EMAIL_TO")

# Stebimų prekių sąrašas (pakeiskite tikromis nuorodomis su https://)
PREKES = {
    "Senukai": {
        "preke": "Medelių putplastis 10cm",
        "url": "https://www.senukai.lt",  # <--- Čia įrašykite tikrą Senukų nuorodą
    },
    "Ermitazas": {
        "preke": "Medelių putplastis 10cm",
        "url": "https://www.ermitazas.lt",  # <--- Čia įrašykite tikrą Ermitažo nuorodą
    },
}

CSV_FAILAS = "kainu_istorija.csv"
siandien = datetime.now().strftime("%Y-%m-%d")


def gauti_kaina_per_scrapingbee(url):
  """Funkcija per ScrapingBee atsisiunčia puslapį ir ištraukia kainą"""
  # Jei nuoroda dar nepakeista, grąžinam testinę kainą, kad nemestų klaidos
  if "ČIA_" in url or url == "https://www.senukai.lt" or url == "https://www.ermitazas.lt":
    print("Pastaba: Naudojama pavyzdinė nuoroda. Nepamirškite įrašyti tikros prekės URL!")
    return 15.99

  api_url = "https://app.scrapingbee.com/api/v1/"
  params = {
      "api_key": SCRAPINGBEE_API_KEY,
      "url": url,
      "render_js": "false",  # Jei puslapis užkrauna kainą su JS, pakeiskite į "true"
  }
  try:
    response = requests.get(api_url, params=params, timeout=30)
    if response.status_code == 200:
      # ČIA PAKEISKITE PAGAL SAVO PUSLAPIO HTML STRUKTŪRĄ (su BeautifulSoup):
      # from bs4 import BeautifulSoup
      # soup = BeautifulSoup(response.text, 'html.parser')
      # kaina_str = soup.find('span', {'class': 'price'}).text
      # return float(kaina_str.replace('€', '').strip().replace(',', '.'))

      return 15.99
    else:
      print(f"Klaida siunčiant užklausą prie {url}: Statuso kodas {response.status_code}")
      return None
  except Exception as e:
    print(f"Klaida jungiantis prie ScrapingBee: {e}")
    return None


# ==========================================
# 2. DUOMENŲ SURINKIMAS IR CSV PILDYMAS
# ==========================================
file_exists = os.path.isfile(CSV_FAILAS)
nauji_duomenys = []

print("Pradedamas kainų tikrinimas...")

for parduotuve, info in PREKES.items():
  print(f"Tikrinama: {parduotuve} - {info['preke']}...")
  kaina = gauti_kaina_per_scrapingbee(info["url"])

  if kaina is not None:
    nauji_duomenys.append({
        "Data": siandien,
        "Parduotuve": parduotuve,
        "Preke": info["preke"],
        "Kaina_Eur": f"{kaina:.2f}",
    })

# Įrašome į CSV failą (Data ir Parduotuvė atskiruose stulpeliuose)
if nauji_duomenys:
  with open(CSV_FAILAS, mode="a", encoding="utf-8", newline="") as f:
    import csv

    writer = csv.writer(f)

    # Jeigu failas naujas, sugeneruojame stulpelių antraštes
    if not file_exists:
      writer.writerow(["Data", "Parduotuve", "Preke", "Kaina_Eur"])

    for d in nauji_duomenys:
      writer.writerow([d["Data"], d["Parduotuve"], d["Preke"], d["Kaina_Eur"]])

  print("Duomenys sėkmingai atnaujinti CSV faile.")
else:
  print("Nebuvo gauta jokių naujų duomenų rašymui į CSV.")

# ==========================================
# 3. SIUNTIMAS EL. PAŠTU (Pasirinktinai)
# ==========================================
if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
  print("Nenurodyti el. pašto nustatymai GitHub Secrets – laiškas nebus siunčiamas, bet skriptas baigė darbą sėkmingai.")
else:
  try:
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = f"Kainų ataskaita ({siandien})"

    # Laiško tekstas
    tekstas = f"Sveiki,\n\nŠtai šios dienos ({siandien}) kainų ataskaita:\n\n"
    for d in nauji_duomenys:
      tekstas += f"- {d['Parduotuve']} ({d['Preke']}): {d['Kaina_Eur']} €\n"
    tekstas += "\nPrisegtuose dokumentuose rasite pilną kainų istorijos CSV failą.\n\nPagarbiai,\nJūsų kainų agentas"

    msg.attach(MIMEText(tekstas, "plain", "utf-8"))

    # Prisegame istorijos CSV failą
    if os.path.isfile(CSV_FAILAS):
      with open(CSV_FAILAS, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

      encoders.encode_base64(part)
      part.add_header("Content-Disposition", f"attachment; filename= {CSV_FAILAS}")
      msg.attach(part)

    # Siuntimas per Gmail SMTP
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
    server.quit()
    print("El. laiškas su ataskaita sėkmingai išsiųstas!")
  except Exception as e:
    print(f"Klaida siunčiant el. laišką: {e}")
