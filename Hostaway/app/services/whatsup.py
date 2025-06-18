from dotenv import load_dotenv
import requests
from app.logging_to_file import setup_logger
import os
import re

logger = setup_logger(__name__)
load_dotenv()

WHATSUP_PHONE_ID = os.getenv('WHATSUP_PHONE_ID')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')


url = f'https://api.wazzup24.com/v3/message'

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}


def send_message(number: str, type: str) -> None | int:
    phone = re.sub(r'\D', '', number)

    template_map = {
        "docs": "f008ffa8-f8b3-4d7c-a1ec-b729d7bd2604",
        "reg": "0522cdb2-d428-4379-af5c-542788e1c4dc",
        "docs_reg": "f61aacc9-18d7-49c7-9ebb-fdd34906a8e5"
    }

    data = {
        "channelId": "86e0768b-4b93-4e52-bc88-2bce2ba9f0a1",
        "crmUserId": "2e0df233-0e31-470f-9b36-0699f34c3b12",
        "chatId": f"380991570383",
        "templateId": template_map.get(type, "123"),
        "chatType": "whatsapp"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.ok:
            print(response.status_code)
        else:
            logger.warning(f"Failed to send message: {response.status_code} {response.text}")
            print (response.status_code)

    except Exception as e:
        logger.warning(f"Error sending message: {e}")
        return None
