import asyncio
from typing import List, Dict
import requests
import os
from dotenv import load_dotenv
import db.nocodb as db
from datetime import date, timedelta, datetime, time
from fastapi import Request
import pytz
from logging_to_file import setup_logger


logger = setup_logger(__name__)
load_dotenv()

BAD_STATUSES = {"cancelled", "declined", "expired", "inquiryDenied", "inquiryNotPossible"}
GET_RESERVATION_BY_ID = "https://api.hostaway.com/v1/reservations"

session = requests.Session()
session.headers.update({
    'Authorization': f"Bearer {os.getenv('HOSTAWAY_API_KEY')}",
    'Cache-control': "no-cache"
})


def get_days(days: int):
    today = date.today()
    today_plus_2 = today + timedelta(days=days)
    return today.strftime("%Y-%m-%d"), today_plus_2.strftime("%Y-%m-%d")


def get_session_url(action: str) -> str:
    if action == "registrations":
        start_date, end_date = get_days(2)
    else:
        start_date, end_date = get_days(1)
    url = (f"https://api.hostaway.com/v1/reservations?"
           f"offset=0&sortOrder=arrivalDate"
           f"&arrivalStartDate={start_date}&arrivalEndDate={end_date}")
    return url


def list_reservations(action: str) -> list:
    valid_reservations = []
    url = get_session_url(action)

    try:
        logger.debug(f"Fetching reservations from URL: {url}")

        response = session.get(url)
        response.raise_for_status()

        json_data = response.json()
        result = json_data.get("result", [])

        for index, reservation in enumerate(result):
            status = reservation.get("status")
            if status not in BAD_STATUSES:
                valid_reservations.append(reservation)

        return valid_reservations

    except Exception as e:
        logger.error(f"Failed to fetch reservations from {url}: {e}", exc_info=True)
        raise


def check_registrations() -> dict:
    response = {}

    try:
        reservations = list_reservations("registrations")

        for reservation in reservations:

            reservation_id = reservation.get("id")

            custom_fields = reservation['customFieldValues']
            checkin_status = next(
                (f['value'] for f in custom_fields if f['customField']['name'] == 'Check-in Online Status'),
                None
            )

            if checkin_status != "GUESTS_REGISTERED":
                if not db.was_reminder_sent(int(reservation_id), "checked_reservations"):
                    response[reservation_id] = "already sent"
                else:
                    response[reservation_id] = db.no_register_answer()
            else:
                response[reservation_id] = "Registered"

        return response

    except Exception as e:
        logger.warning(f"Request failed: {e}")
        raise


def check_verifications() -> dict:
    response = {}

    reservations = list_reservations("verifications")

    for reservation in reservations:

        reservation_id = reservation.get("id")

        custom_fields = reservation['customFieldValues']
        checkin_status = next(
            (f['value'] for f in custom_fields if f['customField']['name'] == 'Identity Verification Status'),
            None
        )

        if checkin_status != "VERIFIED":
            if not db.was_reminder_sent(int(reservation_id), "checked_verifications"):
                response[reservation_id] = "already sent"
            else:
                response[reservation_id] = db.no_documents_answer()
        else:
            response[reservation_id] = "Verified"

    return response


async def webhook(request: Request):
    data = await request.json()

    id = data.get('result').get('id')
    arrival_date = data.get('result').get('arrivalDate')

    if not arrival_date:
        return {"error": "checkin_date missing"}

    checkin_date = datetime.fromisoformat(arrival_date.replace("Z", "+00:00"))
    now = datetime.now(tz=pytz.UTC)

    if checkin_date < now + timedelta(days=1):
        await process_reservation_with_delay(id)
        return {"status": "processing scheduled"}
    else:
        return {"status": "more than a day"}


async def process_reservation_with_delay(id: int):
    try:
        await asyncio.sleep(15 * 60)
        data = session.get(f"{GET_RESERVATION_BY_ID}/{id}").json()

        custom_fields = data['result']['customFieldValues']

        register_check = ((f['value'] for f in custom_fields if f['customField']['name'] == 'Check-in Online Status'),
                          None)
        verification_check = ((f['value'] for f in custom_fields if f['customField']['name'] == 'Identity Verification Status'),
                          None)

        if not register_check and not verification_check:
            return {"message": "register and upload documents"}

        elif not register_check:
            return {"message": "register"}

        elif not verification_check:
            return {"message": "verify"}

        else:
            return {"message": "fine!"}

    except Exception as e:
        logger.error(f"Failed to process reservation: {e}", exc_info=True)














