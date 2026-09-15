import csv
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib
import subprocess
from bs4 import BeautifulSoup
from urllib.parse import quote
import requests  # <--- Štai šio importo trūko faile!

parduotuves = {
    "Senukai": (
        "https://www.senukai.lt/p/putplastis-bewi-eps100-100-cm-x-100-cm-x-10"
        "-cm/e69k?mtd=searchPage&src=lupasearch"
    ),
    "Ermitazas": (
        "https://www.ermitazas.lt/p/polistireninio-putplascio-plokste-termoporas-EPS100-100-x-1000-x-1000-mm-crd62v6v"
    ),
    "ViskasNamams": (
        "https://viskasnamams.lt/p/polistirolas-eps100-100-x-1000-x-1000-mm-1-210"
    ),
    "MokiVezi": (
        "https://mokivezi.lt/1065467-polistireninis-putplastis-etna-eps-100-matmenys-100-x-1000-x-1200-mm-1pak-0-72-m3"
    ),
}

FAILO_VARDAS = "kainu_istorija.csv"


def patikrinti_putplascio_kainas():
  api_key = os.getenv("SCRAPINGBEE_API_KEY")
  if not api_key:
    print("Klaida: nerastas SCRAPINGBEE_API_KEY!")
    return []

  rezultatai = []
  siandien = datetime.now().strftime("%Y-%m-%d")

  for parduotuve, url in parduotuves.items():
    print(f"Jungiamasi prie {parduotuve}...")
    try:
      encoded_url = quote(url, safe="")
      scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={api_key}&url={encoded_url}&render_js=false"

      response = requests.get(scrapingbee_url, timeout=30)

      if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        pavadinimas, kaina = None, None

        h1_el = soup.select_one("h1")
        if h1_el:
          pavadinimas = h1_el.get_text(strip=True)

        if parduotuve == "Senukai":
          for el in soup.find_all(["span", "div", "p"]):
            t = el.get_text(strip=True)
            if (
                ("€" in t or "EUR" in t)
                and len(t) < 20
                and any(c.isdigit() for c in t)
            ):
              kaina = t
              break
        elif parduotuve == "Ermitazas":
          for el in soup.find_all(["span", "div", "strong"]):
            t = el.get_text(strip=True)
            if (
                len(t) in [4, 5, 6]
                and t.replace(".", "").replace(",", "").isdigit()
                and int(t) > 10
            ):
              if "." not in t and "," not in t:
                kaina = f"{t[:-2]},{t[-2:]} €"
              else:
                kaina = t + " €"
              break
        elif parduotuve == "ViskasNamams":
          for el in soup.find_all(["span", "div", "strong"]):
            t = el.get_text(strip=True)
            if (
                "€" in t
                and "/" in t
                and any(c.isdigit() for c in t)
                and len(t) < 25
            ):
              kaina = t
              break
        elif parduotuve == "MokiVezi":
          for el in soup.find_all(["span", "div", "strong", "b"]):
            t = el.get_text(strip=True)
            if ("€" in t or "pak" in t.lower()) and len(t) < 15 and any(
                c.isdigit() for c in t
            ):
              skaitmenys = "".join([c for c in t if c.isdigit()])
              if len(skaitmenys) == 4:
                kaina = f"{skaitmenys[:-2]},{skaitmenys[-2:]} € / pak."
                break
              elif "€" in t:
                kaina = t
                break

        if pavadinimas and kaina:
          rezultatai.append({
              "Data": siandien,
              "Parduotuve": parduotuve,
              "Prekė": pavadinimas[:50],
              "Kaina": kaina,
          })
          print(f"-> {parduotuve}: Rasta kaina {kaina}")
      else:
        print(
            f"-> {parduotuve}: Praleista (statusas {response.status_code})"
        )
    except Exception as e:
      print(f"-> {parduotuve}: Klaida - {e}")

  return rezultatai


def atnaujinti_istorija_ir_irasyti(nauji_duomenys):
  istorija = []

  if os.path.exists(FAILO_VARDAS):
    with open(FAILO_VARDAS, mode="r", encoding="utf-8-sig") as f:
      reader = csv.reader(f, delimiter=";")
      next(reader, None)
      for row in reader:
        if len(row) >= 4:
          istorija.append({
              "Data": row[0],
              "Parduotuve": row[1],
              "Prekė": row[2],
              "Kaina": row[3],
          })

  for r in nauji_duomenys:
    istorija.append(r)

  with open(FAILO_VARDAS, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerow(["Data", "Parduotuve", "Preke", "Kaina"])
    for item in istorija:
      writer.writerow(
          [item["Data"], item["Parduotuve"], item["Prekė"], item["Kaina"]]
      )

  return FAILO_VARDAS


def commit_and_push_csv():
  try:
    subprocess.run(
        ["git", "config", "--global", "user.name", "Kainu Agentas"], check=True
    )
    subprocess.run(
        ["git", "config", "--global", "user.email", "agent@github.action"],
        check=True,
    )
    subprocess.run(["git", "add", FAILO_VARDAS], check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    if status.stdout.strip():
      subprocess.run(
          ["git", "commit", "-m", "Automatinis kainų istorijos atnaujinimas"],
          check=True,
      )
      subprocess.run(["git", "push"], check=True)
      print(
          "Kainų istorijos failas sėkmingai atnaujintas GitHub"
          " repozitorijoje!"
      )
    else:
      print("Jokių naujų pokyčių istorijos failyje.")
  except Exception as e:
    print(f"Nepavyko automatiškai įkelti failo į GitHub: {e}")


def siusti_el_pasta(nauji_duomenys):
  sender_email = os.getenv("GMAIL_USER")
  sender_password = os.getenv("GMAIL_PASSWORD")

  if not sender_email or not sender_password:
    print("Klaida: Nerasti el. pašto kintamieji.")
    return

  csv_kelias = atnaujinti_istorija_ir_irasyti(nauji_duomenys)
  commit_and_push_csv()

  siandien = datetime.now().strftime("%Y-%m-%d")

  msg = MIMEMultipart()
  msg["From"] = sender_email
  msg["To"] = sender_email
  msg["Subject"] = f"🏗️ Putplasčio kainos ({siandien})"

  body = f"Sveiki,\n\nŠtai šios dienos ({siandien}) putplasčio kainų apžvalga:\n\n"
  body += f"{'PARDUOTUVĖ':<15} | {'KAINA':<15} | {'PREKĖ':<40}\n"
  body += "-" * 75 + "\n"

  for r in nauji_duomenys:
    body += f"{r['Parduotuve']:<15} | {r['Kaina']:<15} | {r['Prekė']:<40}\n"

  body += "\nPrisegtame faile rasite visą kainų istoriją nuo pat pradžių."
  msg.attach(MIMEText(body, "plain"))

  try:
    with open(csv_kelias, "rb") as attachment:
      part = MIMEBase("application", "octet-stream")
      part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition", f"attachment; filename= {csv_kelias}"
    )
    msg.attach(part)
  except Exception as e:
    print(f"Nepavyko pridėti failo: {e}")
    return

  try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, sender_email, msg.as_string())
    server.quit()
    print("El. laiškas sėkmingai išsiųstas!")
  except Exception as e:
    print(f"Nepavyko išsiųsti el. pašto: {e}")


if __name__ == "__main__":
  gauti_duomenys = patikrinti_putplascio_kainas()
  if gauti_duomenys:
    siusti_el_pasta(gauti_duomenys)
  else:
    print("Kainų nerasta, laiškas nesiunčiamas.")
