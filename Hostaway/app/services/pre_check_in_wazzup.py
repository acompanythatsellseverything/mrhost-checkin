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


def send_message(number: str, type: str, country: str) -> None | int:
    print(f'message sent')
    phone = re.sub(r'\D', '', number)

    template_map = {
        "reg": {
            "FR": "5508a5b0-a5fe-4ecf-831a-4c25d465bf1e",
            "UA": "11fa6e33-ac69-4bf5-8093-3073eed69a85",
            "RU": "96b2ec86-b908-40f7-8933-62782146032e",
            "NL": "ea452adf-0b10-48c2-953f-32199171e3f7",
            "DE": "c1c30f5d-f697-4a3d-b6ee-ea5cf2317063",
            "ES": "c1c30f5d-f697-4a3d-b6ee-ea5cf2317063",
            "IT": "ba75cf4b-1f3c-446c-9834-55792c0f2852",
            "EN": "0522cdb2-d428-4379-af5c-542788e1c4dc"
        },
        "docs": {
            "FR": "e30287b9-ed11-469d-bb79-d6f18df2df55",
            "UA": "2bf6d09d-b309-4e58-a287-96446d2532bf",
            "RU": "b85f6225-97cd-4c12-aee1-994736f1e727",
            "NL": "3d764fe6-c315-4c09-b0b4-7904ae099076",
            "DE": "cd931109-4be7-4ac8-a31f-45c19d10904a",
            "ES": "d9d01953-4775-436c-86a8-6b5210162348",
            "IT": "02c1dc99-04ae-4c57-88cd-0d13e122a6af",
            "EN": "f008ffa8-f8b3-4d7c-a1ec-b729d7bd2604"
        }
    }

    template_id = template_map.get(type, {}).get(country)

    if not template_id:
        template_id = template_map.get(type, {}).get("EN")

    data = {
        "channelId": "86e0768b-4b93-4e52-bc88-2bce2ba9f0a1",
        "crmUserId": "2e0df233-0e31-470f-9b36-0699f34c3b12",
        "chatId": f"380991570383",
        "templateId": template_id,
        "chatType": "whatsapp"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.ok:
            print(response.status_code)
        else:
            logger.warning(f"Failed to send message: {response.status_code} {response.text}")
            print(response.status_code)

    except Exception as e:
        logger.warning(f"Error sending message: {e}")
        return None

