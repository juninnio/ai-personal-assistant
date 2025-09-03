import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')


def new_fetch(credentials: Credentials, email_count: int = 10):
  #creds = get_creds()
  service = build("gmail", "v1", credentials=credentials)

  try:
    results = (
        service.users().messages().list(userId="me", 
                                        labelIds=['INBOX'],
                                        q=f'category:primary before:{tomorrow} after:{yesterday} is:unread', 
                                        maxResults=email_count
                                        ).execute()
    )

    messages = results.get("messages", [])

    if not messages:
        print("No messages found.")
        return []

    processed_messages = []

    for message in messages:
        try:
          msg = (
              service.users().messages().get(userId="me", id=message["id"], format='full').execute()
          )

          msg_json = get_text(msg)
          msg_sender = msg_json.get('sender',"Unknown sender")
          msg_text = msg_json.get('message',"")
          msg_subject = msg_json.get('subject',"")
          text = "\n".join(line.strip() for line in msg_text.splitlines() if line.strip())

          processed_messages.append({'id':message['id'],'sender':msg_sender,'subject':msg_subject, 'text':text})
        except Exception as e:
           continue
           
    return processed_messages
              
  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


def get_text(message):
  payload = message['payload']
  headers = payload.get('headers', [])

  sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), "Unknown Sender")
  subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), "Unknown Sender")

  if payload.get('parts'):
      for part in payload['parts']:
        if part['mimeType'] == 'text/plain':
          return {'sender':sender, 'subject':subject,'message':decode_base64(part['body']['data'])}
        elif part['mimeType'] == 'text/html':
          html = decode_base64(part['body']['data'])
          return {'sender':sender, 'subject':subject,'message':html_to_text(html)}
  else:
    if payload["mimeType"] == "text/plain":
        return {'sender':sender, 'subject':subject,'message':decode_base64(payload["body"]["data"])}
    elif payload["mimeType"] == "text/html":
        html = decode_base64(payload["body"]["data"])
        return {'sender':sender, 'subject':subject,'message':html_to_text(html)}
    
  return {'sender': sender, 'subject':subject, 'message':''}
   

def decode_base64(data):
    return base64.urlsafe_b64decode(data).decode("utf-8")

def html_to_text(html):
    return BeautifulSoup(html, "html.parser").get_text()
