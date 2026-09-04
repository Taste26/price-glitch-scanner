import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re

# ============================================
# ⚙️ LISTE DES PRODUITS À SURVEILLER
# ============================================
PRODUCTS = [
    # Apple
    {"name": "Apple iPhone"},
    {"name": "Apple MacBook"},
    {"name": "Apple iPad"},
    {"name": "Apple Watch"},
    
    # Samsung
    {"name": "Samsung Galaxy"},
    {"name": "Samsung TV"},
    {"name": "Samsung Galaxy Tab"},
    
    # Google
    {"name": "Google Pixel"},
    
    # Sony
    {"name": "Sony PlayStation"},
    {"name": "Sony TV"},
    
    # Microsoft
    {"name": "Microsoft Surface"},
    {"name": "Xbox"},
    
    # Autres
    {"name": "Dell XPS"},
    {"name": "Lenovo ThinkPad"},
    {"name": "HP Spectre"},
    {"name": "Asus ROG"},
]

# ============================================
# FICHIER DE MÉMOIRE (HISTORIQUE DES PRIX)
# ============================================
HISTORY_FILE = "price_history.json"

# ============================================
# 1. RECHERCHE SUR GOOGLE SHOPPING
# ============================================
def search_price_google(product_name):
    if not product_name:
        return None
    search_url = f"https://www.google.com/search?q={product_name.replace(' ', '+')}+prix+France&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(search_url, timeout=8, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                if price_text:
                    return float(price_text)
            # Fallback : cherche un prix dans le texte
            price_pattern = re.compile(r'(\d+[\.,]\d+)\s*€')
            all_text = soup.get_text()
            matches = price_pattern.findall(all_text)
            if matches:
                first_price = matches[0].replace(',', '.')
                return float(first_price)
    except:
        pass
    return None

# ============================================
# 2. RECHERCHE SUR LES SITES FRANÇAIS
# ============================================
def search_price_cdiscount(product_name):
    url = f"https://www.cdiscount.com/recherche/{product_name.replace(' ', '-')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='price')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                if price_text:
                    return float(price_text)
    except:
        pass
    return None

def search_price_fnac(product_name):
    url = f"https://www.fnac.com/recherche/resultats.do?text={product_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='price')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                if price_text:
                    return float(price_text)
    except:
        pass
    return None

# ============================================
# 3. DÉTECTION DES ANOMALIES
# ============================================
def detect_anomaly(product_name, retailer, current_price, history_prices):
    if not history_prices or len(history_prices) < 2:
        return False, 0
    avg_price = sum(history_prices) / len(history_prices)
    if current_price < (avg_price * 0.80):
        discount = round(((avg_price - current_price) / avg_price) * 100)
        return True, discount
    return False, 0

# ============================================
# 4. ENVOI D'ALERTE SUR TELEGRAM
# ============================================
def send_telegram_alert(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("⚠️ Identifiants Telegram non configurés.")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Alerte Telegram envoyée !")
        else:
            print(f"❌ Erreur Telegram : {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")

# ============================================
# 5. FONCTION PRINCIPALE
# ============================================
def main():
    print(f"🕵️ Lancement du scan - {datetime.now().strftime('%H:%M:%S')}")
    
    # Charger l'historique
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = {}
    
    # Pour chaque produit
    for product in PRODUCTS:
        name = product['name']
        print(f"\n🔍 Recherche de : {name}")
        
        found_prices = []
        
        # Recherche sur Google Shopping
        price = search_price_google(name)
        if price:
            found_prices.append(("Google Shopping", price))
            print(f"   ✅ Google : {price}€")
        
        # Recherche sur Cdiscount
        price = search_price_cdiscount(name)
        if price:
            found_prices.append(("Cdiscount", price))
            print(f"   ✅ Cdiscount : {price}€")
        
        # Recherche sur Fnac
        price = search_price_fnac(name)
        if price:
            found_prices.append(("Fnac", price))
            print(f"   ✅ Fnac : {price}€")
        
        if not found_prices:
            print(f"   ❌ Aucun prix trouvé")
            continue
        
        # Initialiser l'historique
        if name not in history:
            history[name] = {}
        
        # Vérifier les anomalies
        for retailer, price in found_prices:
            if retailer not in history[name]:
                history[name][retailer] = []
            
            history[name][retailer].append(price)
            if len(history[name][retailer]) > 10:
                history[name][retailer].pop(0)
            
            is_anomaly, discount = detect_anomaly(name, retailer, price, history[name][retailer])
            
            if is_anomaly:
                message = f"🚨 *ERREUR DE PRIX DÉTECTÉE !*\n"
                message += f"📦 Produit : {name}\n"
                message += f"🏷️ Enseigne : {retailer}\n"
                message += f"💰 Prix normal : ~{round(history[name][retailer][-2])}€\n"
                message += f"🔥 Prix actuel : {price}€\n"
                message += f"📉 Remise : {discount}%\n"
                message += f"🔗 Lien : https://www.google.com/search?q={name.replace(' ', '+')}+prix"
                print(f"🚨 ALERTE ! {discount}% chez {retailer}")
                send_telegram_alert(message)
    
    # Sauvegarder l'historique
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)
    
    print(f"\n✅ Scan terminé - {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 {len(PRODUCTS)} produits analysés.")
    
    # ============================================
    # ENVOI D'UN RÉCAPITULATIF MÊME SANS ALERTE
    # ============================================
    recap_message = f"✅ *Scan terminé avec succès !*\n"
    recap_message += f"📊 {len(PRODUCTS)} produits analysés.\n"
    recap_message += f"🕒 {datetime.now().strftime('%H:%M')}\n"
    recap_message += f"🔍 Aucune anomalie majeure détectée pour l'instant.\n"
    recap_message += f"🤖 Le robot est en ligne et surveille les prix."
    send_telegram_alert(recap_message)

if __name__ == "__main__":
    main()
