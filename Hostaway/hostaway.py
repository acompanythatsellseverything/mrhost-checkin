from typing import Optional
import requests
import asyncio
from datetime import datetime, timedelta
import answers_db as db
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    'Authorization': f"Bearer {os.getenv('HOSTAWAY_API_KEY')}",
    'Cache-control': "no-cache"
}

session = requests.Session()
session.headers.update(headers)


def list_reservations():
    return_list = []
    bad_status = {"cancelled", "declined", "expired", "inquiryDenied", "inquiryNotPossible"}

    resp = session.get("https://api.hostaway.com/v1/reservations?offset=0&sortOrder=arrivalDate&arrivalStartDate=TODAY")
    resp.raise_for_status()
    json_data = resp.json()

    for data in json_data['result']:

        status = data.get('status')

        arrival_date_split = data['arrivalDate'].split('-')
        arrival_date = datetime(int(arrival_date_split[0]), int(arrival_date_split[1]), int(arrival_date_split[2]))
        date_now = datetime.now()

        if date_now < arrival_date and status not in bad_status:
            return_list.append(data)
        else:
            data['guests_status'] = "None"

    return return_list


def check_the_reservation(reservation_id: int) -> str:
    json_data = list_reservations()[reservation_id]
    date_split = json_data['arrivalDate'].split('-')

    arrival_date = datetime(int(date_split[0]), int(date_split[1]), int(date_split[2]))
    date_now = datetime.now()
    time_difference = arrival_date - date_now

    if time_difference < timedelta(days=1):
        if json_data['result']['customFieldValues'][3]['value'] == "VERIFIED":
            return "Fine"
        else:
            return db.no_doc_answer()
    else:
        return "More than 1 day"



