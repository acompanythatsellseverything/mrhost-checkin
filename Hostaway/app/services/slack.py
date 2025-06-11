import os
import requests
from app.logging_to_file import setup_logger
from dotenv import load_dotenv

logger = setup_logger(__name__)
load_dotenv()

SLACK_API = os.getenv('SLACK_API')


def error_notifications(error_message):
    try:
        payload = {"text": error_message}
        response = requests.post(SLACK_API, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(e)
        return False