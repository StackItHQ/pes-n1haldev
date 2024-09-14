from sqlalchemy.orm import Session
from app.services import google_sheets
from app import models

def sync_sheet_to_db(db: Session):
    # Implement logic to sync from Google Sheets to database
    pass

def sync_db_to_sheet(db: Session):
    # Implement logic to sync from database to Google Sheets
    pass