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
CHECK_IN_URL = ""
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
    start_date, end_date = get_days(1)
    if action == "arrivals":
        url = (f"https://api.hostaway.com/v1/reservations?offset=0&sortOrder=arrivalDate&arrivalStartDate={start_date}"
               f"&arrivalEndDate={start_date}")
    else:
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
                reminders_num = db.was_reminder_sent(int(reservation_id), "checked_verifications")
                if reminders_num == 4:
                    logger.info(f"{reservation_id} - all 3 messages has been already sent.")
                    error_notifications(f"{reservation_id} - all 3 messages has been already sent.")
                else:
                    send_message("+380991570383", country, reminders_num, "check-in")
                    logger.info(f"Reminder message {reminders_num} about verification to {phone_number} was just sent.")
                    error_notifications(f"Reminder message {reminders_num} about verification to {phone_number} was just sent.")
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


def arrivals():
    try:
        reservations = list_reservations("arrivals")

        for reservation in reservations:

            reservation_id = reservation.get("id")
            phone_number = reservation.get("phone")
            country = reservation.get("guestCountry")
            arrival_hour = reservation.get("checkInTime")  # e.g., 15
            reservation_date_str = reservation.get("arrivalDate")  # e.g., "2024-07-20"

            # Validation
            if arrival_hour is None or reservation_date_str is None:
                logger.warning(f"{reservation_id} - Missing check-in time or reservation date")
                continue

            # Parse the reservation date string to datetime
            reservation_date = datetime.strptime(reservation_date_str, "%Y-%m-%d")

            # Build full datetime for check-in
            checkin_datetime = reservation_date.replace(hour=arrival_hour, minute=0, second=0)

            # Add 2 hours to check-in time
            deadline = checkin_datetime + timedelta(hours=2)

            now = datetime.now()

            print(f"[DEBUG] Reservation ID: {reservation_id}")
            print(f"[DEBUG] Now: {now}")
            print(f"[DEBUG] Check-in datetime: {checkin_datetime}")
            print(f"[DEBUG] Deadline (check-in + 2h): {deadline}")

            if now >= deadline:
                code = db.arrival_message(int(reservation_id), "post_checkin")
                if code == 200:
                    send_message("+380991570383", country, 0, "post-check-in")
                    logger.info(f"{reservation_id} - post-checkin message was just sent.")
                    error_notifications(f"{reservation_id} - post-checkin message was just sent")

                elif code == 300:
                    logger.info(f"{reservation_id} - arrival message has been already sent.")
                    error_notifications(f"{reservation_id} - arrival message has been already sent.")

                else:
                    logger.error(f"{reservation_id} - Failed to insert value in db. Message not send")
                    error_notifications(f"{reservation_id} - Failed to insert value in db. Message not send")
            else:
                logger.info(f"{reservation_id} - less than 2 hours after the official arrival time")
                error_notifications(f"{reservation_id} - less than 2 hours after the official arrival time")

        return {"status_code": 200}

    except Exception as e:
        logger.warning(f"Request failed: {e}")
        error_notifications(f"Request failed: {e}")
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
            send_message("+380991570383", "docs_reg", country)
            logger.info(f"Reminder message about verification and registration to {phone_number} was just sent.")
            error_notifications(f"Reminder message about verification and registration to {phone_number} was just sent.")

        elif not register_check:
            send_message("+380991570383", "reg", country)
            logger.info(f"Reminder message about registration to {phone_number} was just sent.")
            error_notifications(f"Reminder message about registration to {phone_number} was just sent.")

        elif not verification_check:
            send_message("+380991570383", "docs", country)
            logger.info(f"Reminder message about verification to {phone_number} was just sent.")
            error_notifications(f"Reminder message about verification to {phone_number} was just sent.")

        else:
            error_notifications(f"User have registered and verified in 15 mins")
            logger.info(f"User have registered and verified in 15 mins")

        return {"status_code": 200}

    except Exception as e:
        logger.error(f"Failed to process reservation: {e}", exc_info=True)
        error_notifications(f"Failed to process reservation: {e}")
        return {"status_code": 201}

