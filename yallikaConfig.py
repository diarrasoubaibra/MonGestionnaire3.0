import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

API_KEY = os.getenv('YELLIKA_API_KEY')
API_URL = os.getenv('YELLIKA_API_URL')

def envoyer_sms_api(recipient, sender_id, message):
    url = API_URL
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }

    data = {
        'recipient': recipient,
        'sender_id': sender_id,
        'type': 'plain',
        'message': message,
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()