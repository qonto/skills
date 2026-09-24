#!/usr/bin/env python3
"""Generate fake but realistic receipts (justificatifs) for the demo.

These are demo props for feature A (receipt reading via get_attachment):
- a receipt whose merchant label is cryptic but whose printed ADDRESS lets the skill
  resolve the city (and unlock a mileage claim web-search couldn't find);
- receipts with a clear VAT breakdown for the VAT cross-check.

De-identified: fictional/generic merchants, addresses are real public places unrelated
to any real account. Output: demo/receipts/*.html (print to PDF to attach in Qonto).
"""

import html
from pathlib import Path

OUT = Path(__file__).parent / "receipts"
OUT.mkdir(exist_ok=True)

# (file, merchant, address, city, date, [(item, price)], vat_rate)
RECEIPTS = [
    ("comptoir-du-marche", "Le Comptoir du Marché", "23 Place Drouet d'Erlon", "51100 Reims",
     "22/06/2026", [("Formule déjeuner", 22.00), ("Plat du jour", 18.00), ("Café gourmand", 8.00)], 10,
     "Ambiguous label → the skill reads THIS receipt to find Reims (~145 km from Paris) → mileage."),
    ("brasserie-georges", "Brasserie Georges", "30 Cours de Verdun Perrache", "69002 Lyon",
     "04/06/2026", [("Choucroute Georges", 24.50), ("Menu déjeuner", 32.00), ("Boissons", 38.50)], 10,
     "Corroborates the Lyon client trip (lunch + hotel + fuel)."),
    ("fnac", "FNAC", "74 Avenue des Champs-Élysées", "75008 Paris",
     "13/06/2026", [("Écran externe 24\"", 109.00), ("Câble HDMI 2.1", 20.00)], 20,
     "Clear VAT line for the VAT cross-check; under €500 HT → immediate deduction."),
]


def render(fname, merchant, address, city, date, items, vat_rate, note):
    total = sum(p for _, p in items)
    ht = round(total / (1 + vat_rate / 100), 2)
    vat = round(total - ht, 2)
    rows = "".join(
        f"<tr><td>{html.escape(label)}</td><td class='r'>{price:.2f} €</td></tr>"
        for label, price in items
    )
    doc = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>Reçu — {html.escape(merchant)}</title>
<style>
  body {{ font-family: 'Courier New', monospace; background:#eee; margin:0; padding:24px; }}
  .receipt {{ width:320px; margin:0 auto; background:#fff; padding:22px 20px;
    box-shadow:0 2px 12px rgba(0,0,0,.15); color:#111; }}
  h1 {{ font-size:17px; text-align:center; margin:0 0 2px; letter-spacing:.5px; }}
  .addr {{ text-align:center; font-size:11px; color:#333; margin:0 0 14px; line-height:1.4; }}
  .meta {{ font-size:11px; color:#333; border-top:1px dashed #999; border-bottom:1px dashed #999;
    padding:6px 0; margin-bottom:10px; display:flex; justify-content:space-between; }}
  table {{ width:100%; border-collapse:collapse; font-size:12px; }}
  td {{ padding:3px 0; }}
  .r {{ text-align:right; }}
  .tot {{ border-top:1px dashed #999; margin-top:8px; padding-top:8px; font-size:12px; }}
  .tot .g {{ font-weight:bold; font-size:14px; }}
  .foot {{ text-align:center; font-size:10px; color:#666; margin-top:14px; }}
  .note {{ width:320px; margin:12px auto 0; font-size:10px; color:#888; text-align:center; font-family:sans-serif; }}
</style></head><body>
  <div class="receipt">
    <h1>{html.escape(merchant.upper())}</h1>
    <p class="addr">{html.escape(address)}<br>{html.escape(city)}<br>Tél. 03 26 00 00 00</p>
    <div class="meta"><span>{date}</span><span>Table 12 · CB</span></div>
    <table>{rows}</table>
    <div class="tot">
      <table>
        <tr><td>Total HT</td><td class="r">{ht:.2f} €</td></tr>
        <tr><td>TVA {vat_rate}%</td><td class="r">{vat:.2f} €</td></tr>
        <tr class="g"><td>TOTAL TTC</td><td class="r">{total:.2f} €</td></tr>
      </table>
    </div>
    <p class="foot">Merci de votre visite — TVA FR00 000 000 000</p>
  </div>
</body></html>"""
    (OUT / f"{fname}.html").write_text(doc, encoding="utf-8")
    return fname, city, total, vat


def main():
    print("Generated demo receipts → demo/receipts/")
    for spec in RECEIPTS:
        fname, city, total, vat = render(*spec)
        print(f"  {fname}.html  ·  {city}  ·  {total:.2f} € (VAT {vat:.2f})")


if __name__ == "__main__":
    main()
