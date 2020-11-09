import telerivet
import time
import json
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.environ.get('API_KEY')
PROJECT_ID = os.environ.get('PROJECT_ID')

tr = telerivet.API(API_KEY)
project = tr.initProjectById(PROJECT_ID)


def get_contacts():

    contactsCursor = project.queryContacts(last_message_time = {'min': 1599638400})

    contacts = []

    for contact in contactsCursor:
        obj = {}
        obj['id'] = contact.id
        obj['phone_number'] = contact.phone_number
        obj['family_name'] = contact.vars.family_name
        obj['first_name'] = contact.vars.first_name
        obj['gender'] = contact.vars.gender
        obj['day'] = contact.vars.day
        obj['arrival'] = contact.vars.arrival
        obj['is_tester'] = contact.vars.is_tester
        obj['last_called'] = contact.vars.last_called
        contacts.append(obj)

    with open('contacts.json', 'w') as outfile:
        json.dump(contacts, outfile)
