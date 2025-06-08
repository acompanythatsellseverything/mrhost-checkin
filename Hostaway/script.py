import requests
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler

session = requests.Session()
scheduler = BackgroundScheduler()

session.headers.update({
    'Authorization': f"Bearer {os.getenv('HOSTAWAY_API_KEY')}",
    'Cache-control': "no-cache"
})


def visit_registration_endpoint():
    try:
        response = session.get("http://127.0.0.1:8000/check_verifications")
        data = response.json()
        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        print(f"Visited endpoint, response:\n{pretty}")
    except Exception as e:
        print(f"Error visiting endpoint: {e}")


def visit_verification_endpoint():
    try:
        response = session.get("http://127.0.0.1:8000/check_verifications")
        data = response.json()
        pretty = json.dumps(data, indent=4, ensure_ascii=False)
        print(f"Visited endpoint, response:\n{pretty}")
    except Exception as e:
        print(f"Error visiting endpoint: {e}")


scheduler.add_job(visit_registration_endpoint, 'cron', hour='13,14,0', minute='0,50')
scheduler.add_job(visit_verification_endpoint, 'cron', hour='8,14,0', minute='0,24')
