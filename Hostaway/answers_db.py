from imports import *
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = f"{os.getenv('API_URL')}"
API_KEY = f"{os.getenv('DB_API_KEY')}"


def no_doc_answer() -> str:
    headers = {
        "xc-token": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(API_URL, headers=headers)

    data = response.json()
    return data['list'][0]['answer']


def checkout_answer() -> str:
    headers = {
        "xc-token": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(API_URL, headers=headers)

    data = response.json()
    return data['list'][3]['answer']

