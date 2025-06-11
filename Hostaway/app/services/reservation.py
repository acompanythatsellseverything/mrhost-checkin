import asyncio
import requests
import os
from dotenv import load_dotenv
import app.db.nocodb as db
from datetime import date, timedelta, datetime
from fastapi import Request
import pytz
from app.logging_to_file import setup_logger
from app.services.slack import error_notifications


logger = setup_logger(__name__)
load_dotenv()

BAD_STATUSES = {"cancelled", "declined", "expired", "inquiryDenied", "inquiryNotPossible"}
GET_RESERVATION_BY_ID = "https://api.hostaway.com/v1/reservations"
CHECK_OUT_URL = "https://api.hostaway.com/v1/reservations?departureStartDate=TODAY&departureEndDate=TODAY"
WEBHOOK_URL = "https://mrhost.top/webhook/34d808dc-03c7-41cd-a426-cae0d7be98f0"

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
        error_notifications(f"Failed to fetch reservations from {url}: {e}")
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
        error_notifications(f"Request failed: {e}")
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


def checkout():
    try:
        response = session.get(CHECK_OUT_URL)
        response.raise_for_status()
        data = response.json()

        for reservation in data.get('result', []):
            reservation_id = reservation.get('id')
            phone = reservation.get('phone')

            if not reservation_id:
                logger.warning("Missing reservation ID, skipping.")
                continue

            conv_url = f"https://api.hostaway.com/v1/reservations/{reservation_id}/conversations"
            conv_response = session.get(conv_url)
            conv_response.raise_for_status()
            conv_data = conv_response.json()

            try:
                conversation_id = conv_data['result'][0]['conversationMessages'][0]['conversationId']
            except (IndexError, KeyError):
                logger.warning(f"No conversation ID found for reservation {reservation_id}")
                error_notifications(f"No conversation ID found for reservation {reservation_id}")
                continue

            msg_url = f"https://api.hostaway.com/v1/conversations/{conversation_id}/messages?limit=5"
            msg_response = session.get(msg_url)
            msg_response.raise_for_status()
            messages_data = msg_response.json()

            messages = "".join(m.get('body', '') for m in messages_data.get('result', []))

            data_send = {
                'conversation_id': conversation_id,
                'phone': phone,
                'messages': messages
            }
            logger.info(f"Sending data: {data_send}")
            try:
                response = requests.post(WEBHOOK_URL, json=data_send)
                response.raise_for_status()
                logger.info(f"Webhook POST successful: {response.status_code}")

            except Exception as e:
                logger.error(f"Webhook POST failed: {e}")
                error_notifications(f"Webhook POST failed: {e}")

        return {"status_code": 200}

    except Exception as e:
        logger.error(f"Failed to process checkout: {e}", exc_info=True)
        error_notifications(f"Failed to process checkout: {e}")
        return {"status_code": 201}


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
        error_notifications(f"Failed to process reservation: {e}")












