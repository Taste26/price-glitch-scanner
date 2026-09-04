import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import time
import re

# ============================================
# ⚙️ CONFIGURATION : LISTE DES PRODUITS À SURVEILLER
# ============================================
# 🔥 Remplace ces exemples par les vrais produits qui t'intéressent !
# Pour chaque produit, mets son nom exact et son code EAN (si tu l'as).
# Si tu n'as pas l'EAN, mets "EAN_INCONNU", le robot cherchera via Google.

PRODUCTS = [
    {"name": "iPhone 16 Pro 256GB", "ean": "0190000000000"},
    {"name": "Samsung Galaxy S25 Ultra", "ean": "8800000000000"},
    {"name": "MacBook Pro M4 14", "ean": "0190000000001"},
    {"name": "TV OLED Samsung 65", "ean": "0880000000000"},
    {"name": "PlayStation 5", "ean": "0711719000000"},
    {"name": "Montre Apple Watch Ultra 2", "ean": "0190000000002"},
]

# ============================================
# FICHIER DE MÉMOIRE (HISTORIQUE DES PRIX)
# ============================================
HISTORY_FILE = "price_history.json"

# ============================================
# 1. FONCTIONS POUR CHAQUE ENSEIGNE
# ============================================

def get_price_cdiscount(ean):
    """Cdiscount - API publique"""
    if not ean or ean == "EAN_INCONNU":
        return None
    url = f"https://www.cdiscount.com/api/product/search?q={ean}"
    try:
        response = requests.get(url, timeout=6)
        if response.status_code == 200:
            data = response.json()
            if data.get('products'):
                price = data['products'][0].get('price')
                return float(price) if price else None
    except:
        pass
    return None

def get_price_fnac(ean):
    """Fnac - API publique"""
    if not ean or ean == "EAN_INCONNU":
        return None
    url = f"https://api.fnac.com/v1/product/{ean}?format=json"
    try:
        response = requests.get(url, timeout=6)
        if response.status_code == 200:
            data = response.json()
            price = data.get('price')
            return float(price) if price else None
    except:
        pass
    return None

def get_price_darty(ean):
    """Darty - Scraping HTML"""
    if not ean or ean == "EAN_INCONNU":
        return None
    url = f"https://www.darty.com/nav/recherche/{ean}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='price')
            if not price_elem:
                price_elem = soup.find('meta', {'property': 'product:price:amount'})
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_boulanger(ean):
    """Boulanger - Scraping HTML"""
    if not ean or ean == "EAN_INCONNU":
        return None
    url = f"https://www.boulanger.com/resultats?tr={ean}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='price')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_ldlc(ean):
    """LDLC - Scraping HTML"""
    if not ean or ean == "EAN_INCONNU":
        return None
    url = f"https://www.ldlc.com/recherche/{ean}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='price')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_ruecommerce(ean):
    """Rue du Commerce - Scraping HTML"""
    if not ean or ean == "EAN_INCONNU":
        return None
    url = f"https://www.rueducommerce.fr/recherche/{ean}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='price')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_backmarket(ean):
    """Back Market - Scraping"""
    if not ean or ean == "EAN_INCONNU":
        return None
    url = f"https://www.backmarket.fr/search?q={ean}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', {'data-testid': 'price-amount'})
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_amazon_google(name):
    """Amazon - On passe par Google Shopping (car Amazon bloque les scrapers)"""
    if not name:
        return None
    search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}+Amazon+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(search_url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Recherche du prix dans les résultats Google Shopping
            price_elem = soup.find('span', class_='a8Pemb')
            if not price_elem:
                price_elem = soup.find('b', string=re.compile(r'[\d,.]+\s*€'))
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                if price_text:
                    return float(price_text)
    except:
        pass
    return None

def get_price_apple(name):
    """Apple - Recherche via Google Shopping"""
    if not name:
        return None
    search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}+Apple+Store+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(search_url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_samsung(name):
    """Samsung - Recherche via Google Shopping"""
    if not name:
        return None
    search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}+Samsung+Store+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(search_url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_orange(name):
    """Orange - Via Google Shopping"""
    if not name:
        return None
    search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}+Orange+prix+smartphone&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(search_url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_sfr(name):
    """SFR - Via Google Shopping"""
    if not name:
        return None
    search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}+SFR+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(search_url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_bouygues(name):
    """Bouygues - Via Google Shopping"""
    if not name:
        return None
    search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}+Bouygues+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(search_url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

def get_price_google_global(name):
    """Recherche globale sur Google Shopping (pour Auchan, Carrefour, Leclerc, etc.)"""
    if not name:
        return None
    search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}+prix+France&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(search_url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                return float(price_text)
    except:
        pass
    return None

# ============================================
# 2. DÉTECTION DES ANOMALIES (ERREURS DE PRIX)
# ============================================

def detect_anomaly(product_name, retailer, current_price, history_prices):
    if not history_prices or len(history_prices) < 2:
        return False, 0
    
    avg_price = sum(history_prices) / len(history_prices)
    
    # Si le prix actuel est inférieur à 80% de la moyenne → Erreur de prix !
    if current_price < (avg_price * 0.80):
        discount = round(((avg_price - current_price) / avg_price) * 100)
        return True, discount
    return False, 0

# ============================================
# 3. ENVOI D'ALERTE SUR TELEGRAM
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
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Alerte Telegram envoyée !")
        else:
            print(f"❌ Erreur Telegram : {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")

# ============================================
# 4. FONCTION PRINCIPALE
# ============================================

def main():
    print(f"🕵️ Lancement du scan complet - {datetime.now().strftime('%H:%M:%S')}")
    
    # Charger l'historique des prix
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = {}
    
    # Pour chaque produit dans la liste
    for product in PRODUCTS:
        name = product['name']
        ean = product.get('ean', '')
        
        print(f"\n🔍 Recherche de : {name}")
        
        # Liste pour stocker les prix trouvés
        found_prices = []
        
        # ---------- 1. SITES AVEC API PUBLIQUE ----------
        price = get_price_cdiscount(ean)
        if price:
            found_prices.append(("Cdiscount", price))
            print(f"   ✅ Cdiscount : {price}€")
        
        price = get_price_fnac(ean)
        if price:
            found_prices.append(("Fnac", price))
            print(f"   ✅ Fnac : {price}€")
        
        # ---------- 2. SCRAPING DES SITES FRANÇAIS ----------
        price = get_price_darty(ean)
        if price:
            found_prices.append(("Darty", price))
            print(f"   ✅ Darty : {price}€")
        
        price = get_price_boulanger(ean)
        if price:
            found_prices.append(("Boulanger", price))
            print(f"   ✅ Boulanger : {price}€")
        
        price = get_price_ldlc(ean)
        if price:
            found_prices.append(("LDLC", price))
            print(f"   ✅ LDLC : {price}€")
        
        price = get_price_ruecommerce(ean)
        if price:
            found_prices.append(("Rue du Commerce", price))
            print(f"   ✅ Rue du Commerce : {price}€")
        
        price = get_price_backmarket(ean)
        if price:
            found_prices.append(("Back Market", price))
            print(f"   ✅ Back Market : {price}€")
        
        # ---------- 3. GRANDES MARQUES VIA GOOGLE SHOPPING ----------
        price = get_price_amazon_google(name)
        if price:
            found_prices.append(("Amazon", price))
            print(f"   ✅ Amazon : {price}€")
        
        price = get_price_apple(name)
        if price:
            found_prices.append(("Apple", price))
            print(f"   ✅ Apple : {price}€")
        
        price = get_price_samsung(name)
        if price:
            found_prices.append(("Samsung", price))
            print(f"   ✅ Samsung : {price}€")
        
        # ---------- 4. OPÉRATEURS TÉLECOM ----------
        price = get_price_orange(name)
        if price:
            found_prices.append(("Orange", price))
            print(f"   ✅ Orange : {price}€")
        
        price = get_price_sfr(name)
        if price:
            found_prices.append(("SFR", price))
            print(f"   ✅ SFR : {price}€")
        
        price = get_price_bouygues(name)
        if price:
            found_prices.append(("Bouygues", price))
            print(f"   ✅ Bouygues : {price}€")
        
        # ---------- 5. RECHERCHE GLOBALE (Auchan, Carrefour, Leclerc, etc.) ----------
        price = get_price_google_global(name)
        if price:
            found_prices.append(("Google Shopping (Global)", price))
            print(f"   ✅ Google Shopping : {price}€")
        
        # ---------- ANALYSE DES PRIX TROUVÉS ----------
        if not found_prices:
            print(f"   ❌ Aucun prix trouvé pour {name}")
            continue
        
        # Initialiser l'historique pour ce produit
        if name not in history:
            history[name] = {}
        
        # Pour chaque prix trouvé, vérifier s'il y a une anomalie
        for retailer, price in found_prices:
            if retailer not in history[name]:
                history[name][retailer] = []
            
            history[name][retailer].append(price)
            # Garder seulement les 10 derniers prix
            if len(history[name][retailer]) > 10:
                history[name][retailer].pop(0)
            
            # Détecter une anomalie
            is_anomaly, discount = detect_anomaly(name, retailer, price, history[name][retailer])
            
            if is_anomaly:
                message = f"🚨 *ERREUR DE PRIX DÉTECTÉE !*\n"
                message += f"📦 Produit : {name}\n"
                message += f"🏷️ Enseigne : {retailer}\n"
                message += f"💰 Prix normal : ~{round(history[name][retailer][-2])}€\n"
                message += f"🔥 Prix actuel : {price}€\n"
                message += f"📉 Remise : {discount}%\n"
                message += f"🔗 Lien : https://www.google.com/search?q={name.replace(' ', '+')}+prix"
                print(f"🚨 ALERTE ! {discount}% de remise chez {retailer}")
                send_telegram_alert(message)
    
    # Sauvegarder l'historique
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)
    
    print(f"\n✅ Scan terminé - {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 {len(PRODUCTS)} produits analysés.")

if __name__ == "__main__":
    main()
