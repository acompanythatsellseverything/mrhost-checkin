import asyncio
import requests
import os
from dotenv import load_dotenv
import app.db.nocodb as db
from datetime import date, timedelta, datetime
from fastapi import Request
import pytz
from app.logging_to_file import setup_logger
from app.services.slack_error_handler import error_notifications
from app.services.pre_check_in_wazzup import send_message

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
        error_notifications(f"Fetching reservations from URL: {url}")

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
    try:
        reservations = list_reservations("registrations")

        for reservation in reservations:

            reservation_id = reservation.get("id")
            phone_number = reservation.get("phone")
            country = reservation.get("guestCountry")
            print(phone_number)
            custom_fields = reservation['customFieldValues']
            checkin_status = next(
                (f['value'] for f in custom_fields if f['customField']['name'] == 'Check-in Online Status'),
                None
            )

            if checkin_status != "GUESTS_REGISTERED":
                if not db.was_reminder_sent(int(reservation_id), "checked_reservations"):
                    logger.info(f"{reservation_id} - message has been already sent before.")
                    error_notifications(f"{reservation_id} - message has been already sent before.")
                else:
                    send_message(phone_number, "reg", country)
                    logger.info(f"Reminder message about verification to {phone_number} was just sent.")
                    error_notifications(f"Reminder message about verification to {phone_number} was just sent.")
            else:
                logger.info(f"{reservation_id} - REGISTERED")
                error_notifications(f"{reservation_id} - REGISTERED")

        return {"status_code": 200}

    except Exception as e:
        logger.warning(f"Request failed: {e}")
        error_notifications(f"Request failed: {e}")
        return {"status_code": 201}


def check_verifications() -> dict:
    try:
        reservations = list_reservations("verifications")

        for reservation in reservations:

            reservation_id = reservation.get("id")
            phone_number = reservation.get("phone")
            country = reservation.get("guestCountry")

            print(country)

            custom_fields = reservation['customFieldValues']
            checkin_status = next(
                (f['value'] for f in custom_fields if f['customField']['name'] == 'Identity Verification Status'),
                None
            )

            if checkin_status != "VERIFIED":
                if not db.was_reminder_sent(int(reservation_id), "checked_verifications"):
                    logger.info(f"{reservation_id} - message has been already sent before.")
                    error_notifications(f"{reservation_id} - message has been already sent before.")
                else:
                    send_message(phone_number, "docs", country)
                    logger.info(f"Reminder message about verification to {phone_number} was just sent.")
                    error_notifications(f"Reminder message about verification to {phone_number} was just sent.")
            else:
                logger.info(f"{reservation_id} - VERIFIED")
                error_notifications(f"{reservation_id} - VERIFIED")

        return {"status_code": 200}

    except Exception as e:
        logger.warning(f"Request failed: {e}")
        error_notifications(f"Request failed: {e}")
        return {"status_code": 201}


async def webhook(data: dict):
    id = data.get('id')
    arrival_date = data.get('arrivalDate')

    if not arrival_date:
        error_notifications(f"No arrival date for {id}")
        return {"error": "checkin_date missing"}

    try:
        naive_date = datetime.strptime(arrival_date, "%Y-%m-%d")
        checkin_date = pytz.UTC.localize(naive_date)
    except Exception as e:
        error_notifications(f"Invalid arrival date format for {id}: {arrival_date}")
        return {"error": f"Invalid date format: {str(e)}"}

    now = datetime.now(tz=pytz.UTC)

    if checkin_date <= now + timedelta(days=1):
        logger.info(f"Started processing {id} the reservation.")
        error_notifications(f"Started processing {id} the reservation.")
        await process_reservation_with_delay(id)
    else:
        error_notifications(f"More than one day for registration {id}")
        logger.info(f"More than one day for registration {id}")


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
                error_notifications(f"Webhook POST successful: {response.status_code}")

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
        phone_number = data['result']['phone']
        country = data['result']['guestCountry']

        register_check = next(
            (f['value'] for f in custom_fields if f['customField']['name'] == 'Check-in Online Status'), None)
        verification_check = next(
            (f['value'] for f in custom_fields if f['customField']['name'] == 'Identity Verification Status'), None)

        if not register_check and not verification_check:
            send_message(phone_number, "docs_reg", country)
            logger.info(f"Reminder message about verification and registration to {phone_number} was just sent.")
            error_notifications(f"Reminder message about verification and registration to {phone_number} was just sent.")

        elif not register_check:
            send_message(phone_number, "reg", country)
            logger.info(f"Reminder message about registration to {phone_number} was just sent.")
            error_notifications(f"Reminder message about registration to {phone_number} was just sent.")

        elif not verification_check:
            send_message(phone_number, "docs", country)
            logger.info(f"Reminder message about verification to {phone_number} was just sent.")
            error_notifications(f"Reminder message about verification to {phone_number} was just sent.")

        return {"status_code": 200}

    except Exception as e:
        logger.error(f"Failed to process reservation: {e}", exc_info=True)
        error_notifications(f"Failed to process reservation: {e}")
        return {"status_code": 201}

