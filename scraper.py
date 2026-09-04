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
    {"name": "Apple iPhone"},
    {"name": "Apple MacBook"},
    {"name": "Apple iPad"},
    {"name": "Apple Watch"},
    {"name": "Samsung Galaxy"},
    {"name": "Samsung TV"},
    {"name": "Google Pixel"},
    {"name": "Sony PlayStation"},
    {"name": "Microsoft Surface"},
    {"name": "Dell XPS"},
    {"name": "Lenovo ThinkPad"},
]

# ============================================
# FICHIER DE MÉMOIRE (HISTORIQUE DES PRIX)
# ============================================
HISTORY_FILE = "price_history.json"

# ============================================
# 1. RECHERCHE SUR EBAY (LE PLUS FIABLE POUR LES ROBOTS)
# ============================================
def search_price_ebay(product_name):
    if not product_name:
        return None
    url = f"https://www.ebay.fr/sch/i.html?_nkw={product_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=8, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # eBay utilise la classe "s-item__price"
            price_elem = soup.find('span', class_='s-item__price')
            if price_elem:
                price_text = price_elem.text.strip()
                # On extrait le premier prix (ex: "899,00 EUR" -> 899.00)
                price_match = re.search(r'(\d+[\.,]\d+)', price_text)
                if price_match:
                    price_clean = price_match.group(1).replace(',', '.')
                    return float(price_clean)
    except Exception as e:
        print(f"   ⚠️ Erreur eBay : {str(e)[:30]}")
    return None

# ============================================
# 2. RECHERCHE SUR GOOGLE SHOPPING (TENTATIVE)
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
# 3. RECHERCHE SUR CDISCOUNT & FNAC
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
# 4. DÉTECTION DES ANOMALIES
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
# 5. ENVOI SUR TELEGRAM (AVEC VÉRIFICATION)
# ============================================
def send_telegram_alert(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # Vérification des secrets
    if not token:
        print("❌ TELEGRAM_TOKEN est VIDE ! Vérifie le secret sur GitHub.")
        return
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID est VIDE ! Vérifie le secret sur GitHub.")
        return
    
    print(f"🔑 Token chargé (longueur: {len(token)})")
    print(f"🆔 Chat ID chargé (longueur: {len(str(chat_id))})")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Alerte Telegram envoyée !")
        else:
            print(f"❌ Erreur Telegram : {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")

# ============================================
# 6. FONCTION PRINCIPALE
# ============================================
def main():
    print(f"🕵️ Lancement du scan - {datetime.now().strftime('%H:%M:%S')}")
    
    # ENVOI D'UN MESSAGE DE TEST IMMÉDIAT POUR VÉRIFIER TELEGRAM
    test_message = "🤖 *Bot en cours d'exécution...*\nJe vérifie la connexion."
    send_telegram_alert(test_message)
    
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
        
        # 1. eBay
        price = search_price_ebay(name)
        if price:
            found_prices.append(("eBay", price))
            print(f"   ✅ eBay : {price}€")
        
        # 2. Google Shopping
        price = search_price_google(name)
        if price:
            found_prices.append(("Google Shopping", price))
            print(f"   ✅ Google : {price}€")
        
        # 3. Cdiscount
        price = search_price_cdiscount(name)
        if price:
            found_prices.append(("Cdiscount", price))
            print(f"   ✅ Cdiscount : {price}€")
        
        # 4. Fnac
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
                print(f"🚨 ALERTE ! {discount}% chez {retailer}")
                send_telegram_alert(message)
    
    # Sauvegarder l'historique
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)
    
    print(f"\n✅ Scan terminé - {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 {len(PRODUCTS)} produits analysés.")
    
    recap_message = f"✅ *Scan terminé !*\n📊 {len(PRODUCTS)} produits analysés.\n🕒 {datetime.now().strftime('%H:%M')}"
    send_telegram_alert(recap_message)

if __name__ == "__main__":
    main()
