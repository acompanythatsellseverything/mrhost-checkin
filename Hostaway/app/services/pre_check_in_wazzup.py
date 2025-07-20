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


def send_message(number: str, country: str, reminders_num: int, action) -> None:
    print('message sent')

    phone = re.sub(r'\D', '', number)

    template_map = {
        "check-in": {
            1: {
                "FR": "e0487873-ea24-498a-ad31-88c920f57736",
                "UA": "0981d98c-38b8-457c-957d-3840cd8d1c9e",
                "RU": "cb4c5c48-976f-4812-b440-1ede89080aa9",
                "NL": "f81c5598-33d0-44f0-9128-d9d0f7614d2b",
                "DE": "e0487873-ea24-498a-ad31-88c920f57736",
                "ES": "99339dbd-7763-49cf-81d8-d8a2c81d7fc1",
                "IT": "1e860765-ba4d-4859-b8b8-fb99c6390469",
                "EN": "72b43b08-5f4a-4550-b283-f8784c4308e8"
            },
            2: {
                "EN": "0455b5a4-c32f-405f-bfe9-49323a57aebe",
                "UA": "a6ac6dfb-70ff-457c-b3e1-c9764a090429",
                "RU": "83102eb9-6eb6-4865-ad56-3092938cf2bd",
                "NL": "983d3ca6-bd8d-41d8-83a9-f5dbbc18f3a6",
                "DE": "1ced05f4-82ea-46da-a86d-f9542feef50e",
                "ES": "fb275d37-d60b-4363-9602-a6d433a462b2",
                "IT": "9aa5568d-b857-497b-b961-83b87f48d194",
                "FR": "a09f82d2-ad65-4c0e-afcd-c3b1ac0ac642"
            },
            3: {
                "EN": "a43a7143-a8dc-4492-a881-b3ca2a2b0346",
                "UA": "20f8a36b-115b-4781-a523-03ea92dbf5b2",
                "RU": "1a370b8b-09c4-4070-927f-75b5877734a5",
                "NL": "038070bc-f06c-4551-b2fc-b740a5b746f4",
                "DE": "84c9783a-83d9-46e7-af60-413ee969fa20",
                "ES": "0f8bb484-4de0-4956-8380-5a01fb454748",
                "IT": "a22d6a21-e9c4-460a-a1a7-a565de185a74",
                "FR": "d4a30308-6e66-4de7-be64-c44df72aead6"
            }
        },
        "post-check-in": {
            "EN": "fe8c4fb7-350d-4129-8776-b2921ef6557e",
            "UA": "166a31c5-9c75-4032-b95a-9fac5c3b58e3",
            "RU": "78960521-b983-4974-95d8-270d507c6821",
            "NL": "dcd64f97-5dc6-43ad-8db1-7a34237a4c19",
            "DE": "8ddb8b1b-1317-4344-b167-c08f4ec32a56",
            "ES": "34d25d7e-1a23-462a-9828-7dd52ccb9553",
            "IT": "bac96b65-9461-452d-ad1c-673e309e3b85",
            "FR": "74deda91-4852-4081-a8ee-6bc2e180590a"
        }
    }

    template_id = None

    if action == "check-in":
        reminder_templates = template_map.get(action, {}).get(reminders_num, {})
        template_id = reminder_templates.get(country) or reminder_templates.get("EN")
    elif action == "post-check-in":
        post_templates = template_map.get(action, {})
        template_id = post_templates.get(country) or post_templates.get("EN")

    if not template_id:
        logger.warning(f"No template ID found for {country}, reminder #{reminders_num}")
        return None

    data = {
        "channelId": "86e0768b-4b93-4e52-bc88-2bce2ba9f0a1",
        "crmUserId": "2e0df233-0e31-470f-9b36-0699f34c3b12",
        "chatId": phone,
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

