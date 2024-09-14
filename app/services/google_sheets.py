from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.core.config import settings

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    creds = Credentials.from_authorized_user_file(settings.GOOGLE_SHEETS_CREDENTIALS_FILE, SCOPES)
    return build('sheets', 'v4', credentials=creds)

def read_sheet(service, range):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=settings.SHEET_ID, range=range).execute()
    return result.get('values', [])

def update_sheet(service, range, values):
    body = {
        'values': values
    }
    sheet = service.spreadsheets()
    result = sheet.values().update(
        spreadsheetId=settings.SHEET_ID, range=range,
        valueInputOption='USER_ENTERED', body=body).execute()
    return result