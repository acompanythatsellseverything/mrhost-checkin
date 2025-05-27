import hostaway as host
import time
from datetime import datetime
import pytz

CET = pytz.timezone('Europe/Paris')
TARGET_TIMES_CET = ['08:00', '20:00']


def Task():
    for i in range(len(host.list_reservations())):
        print(str(host.list_reservations()[i]['id']) + host.check_the_reservation(i))


while True:
    now_cet = datetime.now(CET).strftime('%H:%M')
    if now_cet in TARGET_TIMES_CET:
        Task()
        time.sleep(60)
    time.sleep(1)
