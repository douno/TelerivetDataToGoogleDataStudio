from __future__ import print_function

import os.path
from googleapiclient.discovery import build
from google.oauth2 import service_account

from get_contacts import get_contacts

import telerivet
import json
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get('API_KEY')
PROJECT_ID = os.environ.get('PROJECT_ID')


# Contants:
DELIVERED = 'delivered'
FAILED = 'failed'
COMPLETED = 'Completed'
WRONG_NUMBER = 'Wrong Number'
CALL_FAILED = 'Call Failed'
NO_ANSWER = 'No Answer'
DROPPED_OFF = 'Dropped Off'
UNSPECIFIED = 'Unspeficied'
USER_BUSY = 'User Busy'

HIGH_RISK = 'high risk'
MEDIUM_RISK = 'medium risk'
LOW_RISK = 'low risk'


tr = telerivet.API(API_KEY)
project = tr.initProjectById(PROJECT_ID)

get_contacts()


with open('./contacts.json') as json_file:
    contacts = json.load(json_file)


d = datetime.today() - timedelta(hours=5, minutes=0)

messagesCursor = project.queryMessages(
    direction = 'outgoing',
    message_type = 'call',
    time_created = {'min': d.timestamp()}

)


messages = []

for message in messagesCursor:

    time_created = message.time_created
    call_period = message.vars.call_period
    duration = message.duration
    is_forwarded = message.vars.is_forwarded
    status = message.status
    error_message = message.error_message
    covid_tested_option = message.vars.covid_tested_option

    contact_id = message.contact_id
    # Note: Prepend single quote for formatting in google sheet
    phone_number = "'" + message.to_number
    user_type_option = message.vars.user_type_option

    # Symptoms
    cough_option = message.vars.cough_option
    breathing_option = message.vars.breathing_option
    flu_option = message.vars.flu_option
    sore_throat_option = message.vars.sore_throat_option
    taste_option = message.vars.taste_option
    smell_option = message.vars.smell_option
    fatigued_option = message.vars.fatigued_option
    temperature_2_option = message.vars.temperature_2_option
    general_option = message.vars.general_option
    temperature_option = message.vars.temperature_option

    symptoms = [
        cough_option,
        breathing_option,
        flu_option,
        sore_throat_option,
        taste_option,
        smell_option,
        fatigued_option,
        general_option
    ]

    temperatures = [
        temperature_option,
        temperature_2_option
    ]

    fields_to_fill = []
    if time_created > 1599679805 and time_created < 1600587006:
        fields_to_fill = symptoms + [covid_tested_option, temperature_option]
    if time_created > 1600587006:
        fields_to_fill = symptoms + [covid_tested_option] + temperatures


    if status == DELIVERED:
        incomplete = True if any(f is None for f in fields_to_fill) or all(f is None for f in fields_to_fill) else False
    else:
        incomplete = None

    the_time =  time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_created))

    # Contact information
    for c in contacts:
        if c['id'] == contact_id:
            first_name, family_name, gender, arrival, is_tester, day, last_called = c['first_name'], c['family_name'], c['gender'], c['arrival'], c['is_tester'], c['day'], c['last_called']

    full_name = '{} {}'.format(first_name, family_name)

    if status == DELIVERED:
        if user_type_option == "3":
            delivered_call_status = WRONG_NUMBER
        elif incomplete:
            delivered_call_status = DROPPED_OFF
        else:
            delivered_call_status = COMPLETED
    else:
        delivered_call_status = None


    has_symptoms = True if any(s == "1" for s in symptoms) else False

    has_fever = True if any(t in ["2", "3"] for t in temperatures ) else False
    has_low_fever = True if any(t == "2" for t in temperatures ) else False
    has_high_fever = True if any(t == "3" for t in temperatures ) else False


    if has_symptoms or has_fever:
        if has_symptoms and has_fever:
            risk_status = HIGH_RISK
        elif not has_symptoms and not has_fever:
            risk_status = LOW_RISK
        else:
            risk_status = MEDIUM_RISK
    else:
        risk_status = None


    # Call status information
    if status == FAILED:
        full_status = CALL_FAILED
    elif status == 'not_delivered' and error_message == 'NO_ANSWER':
        full_status = NO_ANSWER
    elif status == 'not_delivered' and error_message == 'UNSPECIFIED':
        full_status = UNSPECIFIED
    elif status == 'not_delivered' and error_message == 'USER_BUSY':
        full_status = USER_BUSY
    elif delivered_call_status == COMPLETED:
        full_status = COMPLETED
    elif delivered_call_status == WRONG_NUMBER:
        full_status = WRONG_NUMBER
    elif delivered_call_status == DROPPED_OFF:
        full_status = DROPPED_OFF
    elif status == 'sent':
        full_status = NO_ANSWER
    else:
        full_status = UNSPECIFIED

    # Set symptom values:
    if has_symptoms or has_fever:
        symptom_vals = []
        if cough_option == '1':
            symptom_vals.append('Cough')
        if breathing_option == '1':
            symptom_vals.append('Difficulty Breathing')
        if flu_option == '1':
            symptom_vals.append('Flu')
        if sore_throat_option == '1':
            symptom_vals.append('Sore Throat')
        if taste_option == '1':
            symptom_vals.append('Loss of sense of taste')
        if smell_option == '1':
            symptom_vals.append('Loss of sense of smell')
        if fatigued_option == '1':
            symptom_vals.append('Fatigued')
        if general_option == '1':
            symptom_vals.append('Generally Feeling Unwell')
        if has_low_fever:
            symptom_vals.append('Low fever')
        if has_high_fever:
            symptom_vals.append('High fever')

        separator = ', '
        symptoms = separator.join(symptom_vals)
    else:
        symptoms = None


    message = [
        incomplete,
        the_time,
        call_period,
        duration,
        is_forwarded,
        covid_tested_option,
        first_name,
        family_name,
        gender,
        arrival,
        contact_id,
        phone_number,
        full_name,
        is_tester,
        last_called,
        day,
        user_type_option,
        cough_option,
        breathing_option,
        flu_option,
        sore_throat_option,
        taste_option,
        smell_option,
        fatigued_option,
        temperature_2_option,
        general_option,
        temperature_option,
        has_symptoms,
        has_fever,
        risk_status,
        delivered_call_status,
        status,
        full_status,
        symptoms
    ]

    if not is_tester:
        messages.append(message)


# Google Sheet API:
SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = None
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1BQhKRQ2M16R4J8xXr9pl8U6aN82I6W8qcmC0oLvvIRQ'

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()

request = sheet.values().append(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range="data",
                                valueInputOption="USER_ENTERED",
                                body={"values":messages})
response = request.execute()
