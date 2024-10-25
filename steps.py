import datetime
import logging
from typing import List

import garth
import requests
import os
from getpass import getpass
from garth import DailySteps

logging.basicConfig(level=logging.INFO, format="%(levelname)-s %(message)s")

MOVING_APP_URL_LOGIN = "https://www.reachingapp.com/app/gmc/backend/api/login"
MOVING_APP_URL_STEPS = "https://www.reachingapp.com/app/gmc/backend/api/useractivity"

# Walking challenge START and END date
START_DATE = datetime.date(2024, 10, 21)
END_DATE = datetime.date(2024, 11, 17)

CREDENTIALS_DIRECTORY = f"{os.path.expanduser('~')}/.moving_challenge"

if not os.path.exists(CREDENTIALS_DIRECTORY):
    os.makedirs(CREDENTIALS_DIRECTORY)
try:
    garth.resume(CREDENTIALS_DIRECTORY)
except Exception as e:
    email = input("Enter email address for Garmin: ")
    password = getpass("Enter password for Garmin: ")
    garth.login(email, password)
    garth.save(CREDENTIALS_DIRECTORY)

moving_app_access_token_file = f"{CREDENTIALS_DIRECTORY}/moving_challenge_token.txt"
if os.path.isfile(moving_app_access_token_file):
    moving_app_file = open(moving_app_access_token_file, "r")
    moving_app_access_token = moving_app_file.readline()
    moving_app_file.close()
else:
    credentials = {
        "email": input("Enter email address for Moving challenge app:"),
        "password": getpass("Enter password for Moving challenge app:")
    }
    response = requests.post(MOVING_APP_URL_LOGIN, json=credentials)
    logging.info(f"[MOVING APP AUTHENTICATION]: Server returned '{response.status_code}'")
    moving_app_access_token = f"Bearer {response.json()['access_token']}"
    moving_app_file = open(moving_app_access_token_file, "w+")
    moving_app_file.write(f"{moving_app_access_token}")
    moving_app_file.close()

number_of_challenge_days = (datetime.date.today() - START_DATE).days + 1
# Filter out records that are not important
steps: List[DailySteps] = [step for step in garth.DailySteps.list(period=number_of_challenge_days) if START_DATE <= step.calendar_date <= END_DATE]
for step in steps:
    # Payload data expected from Moving App
    payload = {
        "report_dt": step.calendar_date.strftime("%Y-%m-%d"),
        "activity_id": 2,
        "activity_quantity": step.total_steps
    }
    response = requests.post(MOVING_APP_URL_STEPS, json=payload, headers={"Authorization": f"{moving_app_access_token}"})
    if response.status_code == 200:
        logging.info(f"[MOVING APP] You got '{response.json()['points']}' points for '{step.calendar_date}'")
    else:
        logging.error(f"Error with submit to Moving App server, contact @zan.magerl. Response: '{response.json()}'", )
