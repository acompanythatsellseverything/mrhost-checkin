import requests
import os
import json
import pytz
import time
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from ..logging_to_file import setup_logger
from ..services.slack_error_handler import error_notifications

logger = setup_logger(__name__)
session = requests.Session()
scheduler = BackgroundScheduler()
spain_tz = timezone('Europe/Madrid')

session.headers.update({
    'Authorization': f"Bearer {os.getenv('HOSTAWAY_API_KEY')}",
    'Cache-control': "no-cache"
})


def visit_registration_endpoint():
    try:
        response = session.get("http://web:8003/check_registrations")
        data = response.json()
        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        error_notifications(f"Visited endpoint, response:\n{pretty}")
        logger.info(f"Visited endpoint, response:\n{pretty}")
    except Exception as e:
        error_notifications(f"Error visiting endpoint: {e}")
        logger.error(f"Error visiting endpoint: {e}")


def visit_verification_endpoint():
    try:
        response = session.get("http://web:8003/check_verifications")
        data = response.json()
        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        error_notifications(f"Visited endpoint, response:\n{pretty}")
        logger.info(f"Visited endpoint, response:\n{pretty}")
    except Exception as e:
        error_notifications(f"Error visiting endpoint: {e}")
        logger.error(f"Error visiting endpoint: {e}")


def visit_checkout():
    try:
        response = session.get("https://dev.mrhost.top/checkout")
        data = response.json()
        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        error_notifications(f"Visited endpoint, response:\n{pretty}")
        logger.info(f"Visited endpoint, response:\n{pretty}")
    except Exception as e:
        error_notifications(f"Error visiting endpoint: {e}")
        logger.error(f"Error visiting endpoint: {e}")


def schedule_jobs():
    logger.info("Scheduling background jobs...")

    scheduler.add_job(
        visit_registration_endpoint,
        'cron',
        hour='11,13,18',
        minute='0,08',
        timezone=spain_tz,
        id="visit_registration",
        replace_existing=True
    )
    logger.info("Scheduled job: visit_registration_endpoint")

    scheduler.add_job(
        visit_verification_endpoint,
        'cron',
        hour='11,13,18',
        minute='0,09',
        timezone=spain_tz,
        id="visit_verification",
        replace_existing=True
    )
    logger.info("Scheduled job: visit_verification_endpoint")

    scheduler.add_job(
        visit_checkout,
        'cron',
        hour='12',
        timezone=spain_tz,
        id="visit_checkout",
        replace_existing=True
    )
    logger.info("Scheduled job: visit_checkout")


if __name__ == "__main__":
    logger.info("Scheduler process starting...")
    schedule_jobs()
    scheduler.start()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down.")

