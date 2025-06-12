from dotenv import load_dotenv
import requests
from app.logging_to_file import setup_logger
import os

logger = setup_logger(__name__)
load_dotenv()

WHATSUP_PHONE_ID = os.getenv('WHATSUP_PHONE_ID')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')


url = f'https://graph.facebook.com/v18.0/{WHATSUP_PHONE_ID}/messages'
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}


def send_message(message: str, number: str) -> None | int:
    try:
        data = {
            'messaging_product': 'whatsapp',
            'to': f'whatsapp:{number}',
            'type': 'text',
            'text': {
                'body': message
            }
        }

        response = requests.post(url, headers=headers, json=data)
        if response.ok:
            return response.status_code
        else:
            logger.warning(f"Failed to send message: {response.status_code} {response.text}")
            return response.status_code

    except Exception as e:
        logger.warning(f"Error sending message: {e}")
        return None

