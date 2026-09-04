import requests
import json
import os
from datetime import datetime

# -------- LISTE DES PRODUITS À SURVEILLER (électronique > 50€) --------
PRODUCTS = [
    {"name": "iPhone 15 128GB", "ean": "0190000000000"},
    {"name": "MacBook Air M2", "ean": "0190000000001"},
    {"name": "TV Samsung 55", "ean": "0880000000000"}
]

# -------- FICHIER POUR GARDER L'HISTORIQUE --------
HISTORY_FILE = "price_history.json"

# -------- FONCTION POUR CHERCHER LE PRIX SUR CDISCOUNT --------
def get_price_cdiscount(ean):
    url = f"https://www.cdiscount.com/api/product/search?q={ean}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('products'):
                price = data['products'][0].get('price')
                return float(price)
    except:
        pass
    return None

# -------- FONCTION POUR CHERCHER LE PRIX SUR FNAC --------
def get_price_fnac(ean):
    url = f"https://api.fnac.com/v1/product/{ean}?format=json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = data.get('price')
            return float(price)
    except:
        pass
    return None

# -------- MOTEUR DE DÉTECTION D'ERREUR DE PRIX --------
def detect_anomaly(product_name, current_price, history_prices):
    if not history_prices or len(history_prices) < 2:
        return False, 0
    
    avg_price = sum(history_prices) / len(history_prices)
    
    if current_price < (avg_price * 0.80):
        discount = round(((avg_price - current_price) / avg_price) * 100)
        return True, discount
    return False, 0

# -------- ENVOI D'ALERTE SUR TELEGRAM --------
def send_telegram_alert(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("⚠️ Identifiants Telegram non configurés. Vérifie les secrets GitHub.")
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

# -------- CŒUR DU PROGRAMME --------
def main():
    print(f"🕵️ Lancement du scan - {datetime.now()}")
    
    # Charger l'historique
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    
    # Scraper chaque produit
    for product in PRODUCTS:
        name = product['name']
        ean = product['ean']
        
        print(f"🔍 Recherche de {name}...")
        
        # Test sur Cdiscount
        price = get_price_cdiscount(ean)
        if not price:
            price = get_price_fnac(ean)
        
        if price:
            print(f"   Prix trouvé : {price}€")
            
            # Ajouter à l'historique
            if name not in history:
                history[name] = []
            history[name].append(price)
            if len(history[name]) > 10:
                history[name].pop(0)
            
            # Vérifier l'anomalie
            is_anomaly, discount = detect_anomaly(name, price, history[name])
            
            if is_anomaly:
                message = f"🚨 *ERREUR DE PRIX DÉTECTÉE !*\n"
                message += f"📦 {name}\n"
                message += f"💰 Prix normal : ~{round(history[name][-2])}€\n"
                message += f"🔥 Prix actuel : {price}€\n"
                message += f"📉 Remise : {discount}%\n"
                message += f"🔗 Lien : https://www.cdiscount.com/recherche/{ean}"
                print(f"🚨 ANOMALIE DÉTECTÉE ! {discount}% de remise")
                send_telegram_alert(message)
        else:
            print(f"   ❌ Prix non trouvé pour {name}")
    
    # Sauvegarder l'historique
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)
    
    print(f"✅ Scan terminé - {datetime.now()}")

if __name__ == "__main__":
    main()
