import requests
import json
import os
import random
from datetime import datetime
from bs4 import BeautifulSoup
import re

# ============================================
# ⚙️ LISTE DES MARQUES GÉNÉRIQUES
# (Pas de modèles spécifiques)
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
# FICHIER DE MÉMOIRE
# ============================================
HISTORY_FILE = "price_history.json"
PRICE_THRESHOLD = 50  # On ignore les prix inférieurs à 50€ (accessoires)

# ============================================
# 1. RECHERCHE SUR EBAY (avec filtre de prix)
# ============================================
def search_prices_ebay(product_name):
    """Cherche plusieurs prix sur eBay et filtre ceux < 50€"""
    if not product_name:
        return []
    
    url = f"https://www.ebay.fr/sch/i.html?_nkw={product_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            prices = []
            
            # eBay utilise la classe "s-item__price"
            for price_elem in soup.find_all('span', class_='s-item__price'):
                price_text = price_elem.text.strip()
                # Extraction du nombre (ex: "899,00 EUR" -> 899.00)
                match = re.search(r'(\d+[\.,]\d+)', price_text)
                if match:
                    price_clean = match.group(1).replace(',', '.')
                    price_value = float(price_clean)
                    
                    # 🔥 FILTRE : On ignore les accessoires < 50€
                    if price_value >= PRICE_THRESHOLD:
                        prices.append(price_value)
            
            # On retourne les prix trouvés (triés du plus petit au plus grand)
            return sorted(prices)
    except Exception as e:
        print(f"   ⚠️ Erreur eBay : {str(e)[:50]}")
    
    return []

# ============================================
# 2. RECHERCHE SUR GOOGLE SHOPPING (avec filtre)
# ============================================
def search_prices_google(product_name):
    """Cherche les prix sur Google Shopping et filtre < 50€"""
    if not product_name:
        return []
    
    search_url = f"https://www.google.com/search?q={product_name.replace(' ', '+')}+prix&tbm=shop"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(search_url, timeout=10, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            prices = []
            
            # Recherche des balises contenant des prix
            price_pattern = re.compile(r'(\d+[\.,]\d+)\s*€')
            all_text = soup.get_text()
            matches = price_pattern.findall(all_text)
            
            for match in matches:
                price_clean = match.replace(',', '.')
                price_value = float(price_clean)
                if price_value >= PRICE_THRESHOLD:
                    prices.append(price_value)
            
            return sorted(prices)
    except:
        pass
    
    return []

# ============================================
# 3. ENVOI DE MESSAGE SUR TELEGRAM
# ============================================
def send_telegram(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ Secrets manquants !")
        return False
    
    print(f"🔑 Token chargé (longueur: {len(token)})")
    print(f"🆔 Chat ID chargé (longueur: {len(str(chat_id))})")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message envoyé !")
            return True
        else:
            print(f"❌ Erreur {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

# ============================================
# 4. FONCTION PRINCIPALE
# ============================================
def main():
    print(f"🚀 Scan des marques génériques - {datetime.now().strftime('%H:%M:%S')}")
    
    # --- MESSAGE DE TEST POUR TELEGRAM ---
    print("\n📤 Envoi d'un message de test Telegram...")
    send_telegram("🤖 *Bot allumé !*\nJe recherche les prix pour les marques génériques (Apple, Samsung...)\nLes accessoires < 50€ sont ignorés.")
    
    # Charger l'historique
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = {}
    
    results_summary = []
    
    for brand in PRODUCTS:
        print(f"\n🔍 Recherche de la marque : {brand}")
        
        all_prices = []
        
        # 1. Recherche sur eBay
        ebay_prices = search_prices_ebay(brand)
        if ebay_prices:
            # On prend le prix le plus bas trouvé (après filtrage > 50€)
            lowest_price = ebay_prices[0]
            all_prices.append(("eBay", lowest_price))
            print(f"   ✅ eBay : {lowest_price}€ (et {len(ebay_prices)} autres prix filtrés)")
        else:
            print(f"   ❌ Aucun prix > 50€ sur eBay")
        
        # 2. Recherche sur Google Shopping
        google_prices = search_prices_google(brand)
        if google_prices:
            lowest_price = google_prices[0]
            all_prices.append(("Google Shopping", lowest_price))
            print(f"   ✅ Google : {lowest_price}€")
        else:
            print(f"   ❌ Aucun prix > 50€ sur Google")
        
        if not all_prices:
            print(f"   ❌ Aucun prix trouvé pour {brand}")
            # On envoie un message pour prévenir quand même
            send_telegram(f"⚠️ *Aucun produit trouvé pour {brand}* (prix < 50€ ignorés)")
            continue
        
        # Enregistrement dans l'historique
        if brand not in history:
            history[brand] = {}
        
        for retailer, price in all_prices:
            if retailer not in history[brand]:
                history[brand][retailer] = []
            
            history[brand][retailer].append(price)
            if len(history[brand][retailer]) > 10:
                history[brand][retailer].pop(0)
            
            # Détection d'anomalie (chute de 80%)
            if len(history[brand][retailer]) >= 2:
                avg_price = sum(history[brand][retailer]) / len(history[brand][retailer])
                if price < (avg_price * 0.80):
                    discount = round(((avg_price - price) / avg_price) * 100)
                    alert_msg = f"🚨 *ERREUR DE PRIX !*\n"
                    alert_msg += f"📦 Marque : {brand}\n"
                    alert_msg += f"🏷️ Enseigne : {retailer}\n"
                    alert_msg += f"💰 Prix normal : ~{round(avg_price)}€\n"
                    alert_msg += f"🔥 Prix actuel : {price}€\n"
                    alert_msg += f"📉 Remise : {discount}%"
                    print(f"🚨 ALERTE ! {discount}% chez {retailer}")
                    send_telegram(alert_msg)
        
        # Résumé pour le récapitulatif final
        if all_prices:
            results_summary.append(f"{brand}: {all_prices[0][1]}€ (sur {all_prices[0][0]})")
    
    # Sauvegarde de l'historique
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)
    
    # --- ENVOI DU RÉCAPITULATIF FINAL ---
    recap = "📊 *Récapitulatif du scan*\n\n"
    if results_summary:
        recap += "\n".join(results_summary)
    else:
        recap += "Aucun prix trouvé pour le moment."
    
    recap += f"\n\n🕒 {datetime.now().strftime('%H:%M')}"
    recap += f"\n🔍 {len(PRODUCTS)} marques analysées."
    recap += "\n🤖 Les accessoires < 50€ sont automatiquement ignorés."
    
    print("\n📤 Envoi du récapitulatif final...")
    send_telegram(recap)
    
    print(f"\n✅ Scan terminé - {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
