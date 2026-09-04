import requests
import os
from datetime import datetime

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

def main():
    print(f"🚀 Test de connexion - {datetime.now().strftime('%H:%M:%S')}")
    
    test_msg = "🤖 *Connexion réussie !*\nLe bot est en ligne et peut t'envoyer des alertes."
    
    print("📤 Envoi du message de test...")
    success = send_telegram(test_msg)
    
    if success:
        print("✅ Test réussi ! Tu as reçu le message sur Telegram.")
    else:
        print("❌ Le test a échoué. Vérifie que le token et le chat ID sont bien copiés.")

if __name__ == "__main__":
    main()
