import requests
import json
import os
import re
from datetime import datetime

# ============================================
# MARQUES À SURVEILLER
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

HISTORY_FILE = "price_history.json"

# ============================================
# 1. RECHERCHE DES PRIX VIA DUCKDUCKGO (SANS INSCRIPTION)
# ============================================
def search_price_duckduckgo(brand):
    """
    Cherche le prix sur DuckDuckGo en utilisant l'API instant answer.
    Aucune clé API nécessaire !
    """
    url = f"https://api.duckduckgo.com/?q={brand.replace(' ', '+')}+prix+France&format=json&no_html=1&skip_disambig=1"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # On récupère le texte de la réponse (l'extrait)
        text = data.get("AbstractText", "")
        if not text:
            text = data.get("Answer", "")
        if not text:
            # Si rien, on cherche dans la ligne "RelatedTopics"
            for topic in data.get("RelatedTopics", []):
                if "Text" in topic:
                    text += topic["Text"] + " "
        
        # On cherche un prix dans le texte (ex: "899 euros", "899€", "899.99")
        match = re.search(r'(\d+[\.,]\d*)\s*(?:€|euro|EUR)', text)
        if not match:
            match = re.search(r'(\d+)\s*(?:€|euro|EUR)', text)
        
        if match:
            price_str = match.group(1).replace(',', '.')
            return float(price_str)
    except Exception as e:
        print(f"   ⚠️ Erreur DuckDuckGo : {str(e)[:50]}")
    
    return None

# ============================================
# 2. ENVOI SUR TELEGRAM
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
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram envoyé")
            return True
        else:
            print(f"❌ Erreur {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

# ============================================
# 3. DÉTECTION D'ANOMALIE
# ============================================
def detect_anomaly(history_prices, current_price):
    if not history_prices or len(history_prices) < 2:
        return False, 0
    
    avg_price = sum(history_prices) / len(history_prices)
    if current_price < (avg_price * 0.80):
        discount = round(((avg_price - current_price) / avg_price) * 100)
        return True, discount
    return False, 0

# ============================================
# 4. FONCTION PRINCIPALE
# ============================================
def main():
    print(f"🚀 Scan DuckDuckGo - {datetime.now().strftime('%H:%M:%S')}")
    
    send_telegram("🤖 *Bot démarré* - Recherche des prix via DuckDuckGo (sans inscription)")
    
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = {}
    
    results = []
    alerts = 0
    
    for brand in PRODUCTS:
        print(f"\n🔍 Recherche de {brand}...")
        
        price = search_price_duckduckgo(brand)
        
        if price:
            print(f"   ✅ {price}€ trouvé")
            results.append(f"{brand}: {price}€")
            
            if brand not in history:
                history[brand] = {"DuckDuckGo": []}
            if "DuckDuckGo" not in history[brand]:
                history[brand]["DuckDuckGo"] = []
            
            history[brand]["DuckDuckGo"].append(price)
            if len(history[brand]["DuckDuckGo"]) > 10:
                history[brand]["DuckDuckGo"].pop(0)
            
            is_anomaly, discount = detect_anomaly(history[brand]["DuckDuckGo"], price)
            if is_anomaly:
                avg = round(sum(history[brand]["DuckDuckGo"]) / len(history[brand]["DuckDuckGo"]))
                alert_msg = f"🚨 *ALERTE PRIX !*\n📦 {brand}\n💰 Normal : ~{avg}€\n🔥 Actuel : {price}€\n📉 Remise : {discount}%"
                alerts += 1
                send_telegram(alert_msg)
        else:
            print(f"   ❌ Prix non trouvé")
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)
    
    recap = "📊 *Résumé du scan*\n\n"
    recap += "\n".join(results) if results else "Aucun prix trouvé."
    recap += f"\n\n🕒 {datetime.now().strftime('%H:%M')}"
    recap += f"\n🔍 {len(PRODUCTS)} marques analysées."
    recap += f"\n🚨 {alerts} alerte(s)" if alerts else "\n✅ Aucune alerte."
    
    send_telegram(recap)
    print(f"\n✅ Scan terminé - {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
