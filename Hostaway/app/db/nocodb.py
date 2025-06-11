import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_ANSWERS_URL = f"{os.getenv('API_ANSWERS_URL')}"
API_REMINDERS_URL = f"{os.getenv('API_REMINDERS_URL')}"
API_KEY = f"{os.getenv('DB_API_KEY')}"

headers = {
    "xc-token": API_KEY,
    "Content-Type": "application/json"
}


def no_register_answer() -> str:
    response = requests.get(API_ANSWERS_URL, headers=headers)

    data = response.json()
    return data['list'][16]['answer']


def no_documents_answer() -> str:
    response = requests.get(API_ANSWERS_URL, headers=headers)

    data = response.json()
    return data['list'][0]['answer']


def was_reminder_sent(id: int, table: str) -> bool:
    params = {
        "where": f"(reservation_id,eq,{id})"
    }

    response = requests.get(f"{API_REMINDERS_URL}/{table}", params=params, headers=headers)

    data = response.json()
    rows = data.get("list", [])
    print(rows)

    if rows:
        print(f"ID {id} found.")
        return False
    else:
        new_row = {"reservation_id": id}
        insert_resp = requests.post(f"{API_REMINDERS_URL}/{table}", headers=headers, json=new_row)

        if insert_resp.status_code in (200, 201):
            print(f"ID {id} not found, inserted new row.")

    return True










