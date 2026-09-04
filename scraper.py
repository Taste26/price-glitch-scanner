import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# ============================================
# ⚙️ MARQUES À SURVEILLER (GÉNÉRIQUES)
# ============================================
PRODUCTS = [
    "Apple",
    "Samsung",
    "Google",
    "Sony",
    "Microsoft",
    "Dell",
    "Lenovo",
    "HP",
    "Asus",
    "Xiaomi"
]

# ============================================
# FICHIER D'HISTORIQUE
# ============================================
HISTORY_FILE = "price_history.json"
MIN_PRICE = 50   # Ignorer les accessoires < 50€

# ============================================
# RECHERCHE SUR EBAY (avec filtrage)
# ============================================
def search_prices_ebay(brand):
    if not brand:
        return []
    url = f"https://www.ebay.fr/sch/i.html?_nkw={brand.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, timeout=10, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            prices = []
            for elem in soup.find_all('span', class_='s-item__price'):
                txt = elem.text.strip()
                m = re.search(r'(\d+[\.,]\d+)', txt)
                if m:
                    val = float(m.group(1).replace(',', '.'))
                    if val >= MIN_PRICE:
                        prices.append(val)
            return sorted(prices)
    except:
        pass
    return []

# ============================================
# RECHERCHE SUR GOOGLE SHOPPING (avec filtrage)
# ============================================
def search_prices_google(brand):
    if not brand:
        return []
    url = f"https://www.google.com/search?q={brand.replace(' ', '+')}+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, timeout=10, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            prices = []
            # cherche tous les prix dans le texte
            all_text = soup.get_text()
            for m in re.findall(r'(\d+[\.,]\d+)\s*€', all_text):
                val = float(m.replace(',', '.'))
                if val >= MIN_PRICE:
                    prices.append(val)
            return sorted(prices)
    except:
        pass
    return []

# ============================================
# ENVOI SUR TELEGRAM
# ============================================
def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print("❌ Secrets manquants")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Telegram envoyé")
            return True
        else:
            print(f"❌ Erreur {r.status_code}: {r.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

# ============================================
# FONCTION PRINCIPALE
# ============================================
def main():
    print(f"🚀 Scan des marques - {datetime.now().strftime('%H:%M:%S')}")

    # 1. Message de démarrage
    send_telegram("🤖 *Bot démarré* - Surveillance des prix (Apple, Samsung…)")

    # Charger l'historique
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = {}

    summary = []
    alerts = 0

    for brand in PRODUCTS:
        print(f"\n🔍 {brand}")
        all_prices = []

        # eBay
        ebay = search_prices_ebay(brand)
        if ebay:
            all_prices.append(("eBay", ebay[0]))
            print(f"   ✅ eBay : {ebay[0]}€ ({len(ebay)} prix trouvés)")
        else:
            print("   ❌ eBay : rien")

        # Google
        google = search_prices_google(brand)
        if google:
            all_prices.append(("Google", google[0]))
            print(f"   ✅ Google : {google[0]}€")
        else:
            print("   ❌ Google : rien")

        if not all_prices:
            continue

        # Initialiser l'historique pour cette marque
        if brand not in history:
            history[brand] = {}

        for retailer, price in all_prices:
            if retailer not in history[brand]:
                history[brand][retailer] = []
            history[brand][retailer].append(price)
            if len(history[brand][retailer]) > 10:
                history[brand][retailer].pop(0)

            # Détection d'anomalie (baisse ≥ 80%)
            if len(history[brand][retailer]) >= 2:
                avg = sum(history[brand][retailer]) / len(history[brand][retailer])
                if price < avg * 0.80:
                    disc = round(((avg - price) / avg) * 100)
                    msg = (
                        f"🚨 *ALERTE PRIX !*\n"
                        f"📦 {brand}\n"
                        f"🏷️ {retailer}\n"
                        f"💰 Normal : ~{round(avg)}€\n"
                        f"🔥 Actuel : {price}€\n"
                        f"📉 Remise : {disc}%"
                    )
                    alerts += 1
                    print(f"🚨 ALERTE ! {disc}% sur {brand} ({retailer})")
                    send_telegram(msg)

        # Résumé pour le récapitulatif final
        if all_prices:
            summary.append(f"{brand}: {all_prices[0][1]}€ (via {all_prices[0][0]})")

    # Sauvegarde de l'historique
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

    # Récapitulatif final
    recap = "📊 *Résumé du scan*\n\n"
    recap += "\n".join(summary) if summary else "Aucun prix trouvé."
    recap += f"\n\n🕒 {datetime.now().strftime('%H:%M')}"
    recap += f"\n🔍 {len(PRODUCTS)} marques analysées."
    if alerts:
        recap += f"\n🚨 {alerts} alertes déclenchées !"
    else:
        recap += "\n✅ Aucune alerte pour l'instant."

    send_telegram(recap)
    print(f"\n✅ Scan terminé - {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
