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


def was_reminder_sent(id: int, table: str) -> int:
    params = {
        "where": f"(reservation_id,eq,{id})"
    }

    response = requests.get(f"{API_REMINDERS_URL}/{table}", params=params, headers=headers)
    data = response.json()
    rows = data.get("list", [])

    sent_count = len(rows)

    if sent_count < 3:
        new_row = {"reservation_id": id}
        insert_resp = requests.post(f"{API_REMINDERS_URL}/{table}", headers=headers, json=new_row)

        if insert_resp.status_code in (200, 201):
            print(f"Reminder #{sent_count + 1} sent for reservation {id}.")
            return sent_count + 1

        else:
            print(f"Failed to insert reminder for reservation {id}.")
            return sent_count

    else:
        print(f"Max reminders reached for reservation {id}.")
        return 4


def arrival_message(id: int, table: str) -> int:
    params = {
        "where": f"(reservation_id,eq,{id})"
    }

    response = requests.get(f"{API_REMINDERS_URL}/{table}", params=params, headers=headers)
    data = response.json()
    rows = data.get("list", [])

    sent_count = len(rows)

    if sent_count:
        return 300

    else:
        new_row = {"reservation_id": id}
        insert_resp = requests.post(f"{API_REMINDERS_URL}/{table}", headers=headers, json=new_row)

        if insert_resp.status_code in (200, 201):
            print(f"Arrival message sent for reservation {id}.")
            return 200

        else:
            print(f"Failed to insert id for reservation {id}.")
            return 500










