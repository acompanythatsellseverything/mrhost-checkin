import requests
import os
import json
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from app.logging_to_file import setup_logger

logger = setup_logger(__name__)
session = requests.Session()
scheduler = BackgroundScheduler()

session.headers.update({
    'Authorization': f"Bearer {os.getenv('HOSTAWAY_API_KEY')}",
    'Cache-control': "no-cache"
})


def visit_registration_endpoint():
    try:
        response = session.get("https://dev.mrhost.top/check_registrations")
        data = response.json()
        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        print(f"Visited endpoint, response:\n{pretty}")
    except Exception as e:
        print(f"Error visiting endpoint: {e}")


def visit_verification_endpoint():
    try:
        response = session.get("https://dev.mrhost.top/check_verifications")
        data = response.json()
        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        print(f"Visited endpoint, response:\n{pretty}")
        logger.info(f"Visited endpoint, response:\n{pretty}")
    except Exception as e:
        logger.error(f"Error visiting endpoint: {e}")


def visit_checkout():
    try:
        response = session.get("https://dev.mrhost.top/checkout")
        data = response.json()
        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        logger.info(f"Visited endpoint, response:\n{pretty}")
    except Exception as e:
        logger.error(f"Error visiting endpoint: {e}")


spain_tz = pytz.timezone('Europe/Madrid')

scheduler.add_job(visit_registration_endpoint, 'cron', hour='10,12,18', minute='0,27', timezone=spain_tz)
scheduler.add_job(visit_verification_endpoint, 'cron', hour='10,15,18', minute='0,00', timezone=spain_tz)
scheduler.add_job(visit_checkout, 'cron', hour='12', timezone=spain_tz)