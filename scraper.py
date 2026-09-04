import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time

# ============================================
# ⚙️ LISTE DES PRODUITS À SURVEILLER
# ============================================
# 🔥 Le robot cherchera ces marques sur tous les sites
PRODUCTS = [
    {"name": "iPhone"},
    {"name": "Mac mini"},
    {"name": "MacBook"},
    {"name": "iPad"},
    {"name": "Samsung Galaxy"}
]

# ============================================
# FICHIER DE MÉMOIRE (HISTORIQUE DES PRIX)
# ============================================
HISTORY_FILE = "price_history.json"

# ============================================
# 1. RECHERCHE SUR GOOGLE SHOPPING (LA PLUS FIABLE SANS EAN)
# ============================================

def search_price_google(product_name):
    """Recherche le prix d'un produit sur Google Shopping"""
    if not product_name:
        return None
    
    # On cherche le produit en France
    search_url = f"https://www.google.com/search?q={product_name.replace(' ', '+')}+prix+France&tbm=shop"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(search_url, timeout=8, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Méthode 1 : La classe classique de Google Shopping
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                if price_text:
                    return float(price_text)
            
            # Méthode 2 : Recherche d'un prix dans une balise <b> ou <span>
            price_pattern = re.compile(r'(\d+[\.,]\d+)\s*€')
            all_text = soup.get_text()
            matches = price_pattern.findall(all_text)
            if matches:
                # Prend le premier prix trouvé
                first_price = matches[0].replace(',', '.')
                return float(first_price)
                
    except Exception as e:
        print(f"   ⚠️ Erreur Google : {str(e)[:50]}")
    
    return None

# ============================================
# 2. RECHERCHE SUR LES SITES AVEC LE NOM DU PRODUIT
# (Pour Cdiscount, Fnac, etc. sans EAN, on passe par leur moteur de recherche)
# ============================================

def search_price_cdiscount(product_name):
    """Cdiscount - Recherche par nom"""
    url = f"https://www.cdiscount.com/recherche/{product_name.replace(' ', '-')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Recherche du premier prix affiché
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
    """Fnac - Recherche par nom"""
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

def search_price_darty(product_name):
    """Darty - Recherche par nom"""
    url = f"https://www.darty.com/nav/recherche/{product_name.replace(' ', '+')}"
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

def search_price_boulanger(product_name):
    """Boulanger - Recherche par nom"""
    url = f"https://www.boulanger.com/resultats?tr={product_name.replace(' ', '+')}"
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

def search_price_ldlc(product_name):
    """LDLC - Recherche par nom"""
    url = f"https://www.ldlc.com/recherche/{product_name.replace(' ', '+')}/"
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

def search_price_amazon(product_name):
    """Amazon - Recherche par nom (via une recherche simple)"""
    url = f"https://www.amazon.fr/s?k={product_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Amazon utilise souvent une classe 'a-price-whole'
            price_elem = soup.find('span', class_='a-price-whole')
            if price_elem:
                price_text = re.sub(r'[^\d]', '', price_elem.text.strip())
                if price_text:
                    return float(price_text)
            # Fallback
            price_elem = soup.find('span', class_='a-offscreen')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                if price_text:
                    return float(price_text)
    except:
        pass
    return None

def search_price_apple(product_name):
    """Apple - Recherche par nom (via Google Shopping car le site Apple est verrouillé)"""
    # On utilise Google Shopping spécifiquement pour Apple
    url = f"https://www.google.com/search?q={product_name.replace(' ', '+')}+Apple+Store+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                if price_text:
                    return float(price_text)
    except:
        pass
    return None

def search_price_samsung(product_name):
    """Samsung - Recherche par nom (via Google Shopping)"""
    url = f"https://www.google.com/search?q={product_name.replace(' ', '+')}+Samsung+Store+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, timeout=6, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            price_elem = soup.find('span', class_='a8Pemb')
            if price_elem:
                price_text = re.sub(r'[^\d,.]', '', price_elem.text.strip())
                price_text = price_text.replace(',', '.')
                if price_text:
                    return float(price_text)
    except:
        pass
    return None

# ============================================
# 3. DÉTECTION DES ANOMALIES (ERREURS DE PRIX)
# ============================================

def detect_anomaly(product_name, retailer, current_price, history_prices):
    if not history_prices or len(history_prices) < 2:
        return False, 0
    
    avg_price = sum(history_prices) / len(history_prices)
    
    # 🔥 Détection d'erreur de prix (>= 80% de remise)
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
        print("⚠️ Identifiants Telegram non configurés. Ajoute les secrets sur GitHub.")
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
        
        # --- 1. Google Shopping (le plus fiable sans EAN) ---
        price = search_price_google(name)
        if price:
            found_prices.append(("Google Shopping", price))
            print(f"   ✅ Google : {price}€")
        
        # --- 2. Cdiscount ---
        price = search_price_cdiscount(name)
        if price:
            found_prices.append(("Cdiscount", price))
            print(f"   ✅ Cdiscount : {price}€")
        
        # --- 3. Fnac ---
        price = search_price_fnac(name)
        if price:
            found_prices.append(("Fnac", price))
            print(f"   ✅ Fnac : {price}€")
        
        # --- 4. Darty ---
        price = search_price_darty(name)
        if price:
            found_prices.append(("Darty", price))
            print(f"   ✅ Darty : {price}€")
        
        # --- 5. Boulanger ---
        price = search_price_boulanger(name)
        if price:
            found_prices.append(("Boulanger", price))
            print(f"   ✅ Boulanger : {price}€")
        
        # --- 6. LDLC ---
        price = search_price_ldlc(name)
        if price:
            found_prices.append(("LDLC", price))
            print(f"   ✅ LDLC : {price}€")
        
        # --- 7. Amazon ---
        price = search_price_amazon(name)
        if price:
            found_prices.append(("Amazon", price))
            print(f"   ✅ Amazon : {price}€")
        
        # --- 8. Apple (spécifique) ---
        if "iPhone" in name or "Mac" in name or "iPad" in name:
            price = search_price_apple(name)
            if price:
                found_prices.append(("Apple", price))
                print(f"   ✅ Apple : {price}€")
        
        # --- 9. Samsung (spécifique) ---
        if "Samsung" in name:
            price = search_price_samsung(name)
            if price:
                found_prices.append(("Samsung", price))
                print(f"   ✅ Samsung : {price}€")
        
        # --- Analyse des prix ---
        if not found_prices:
            print(f"   ❌ Aucun prix trouvé pour {name}")
            continue
        
        # Initialiser l'historique pour ce produit
        if name not in history:
            history[name] = {}
        
        # Vérifier chaque prix
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

if __name__ == "__main__":
    main()
