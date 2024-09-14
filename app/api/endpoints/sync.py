from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.sync import sync_sheet_to_db, sync_db_to_sheet

router = APIRouter()

@router.post("/sync")
async def sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(sync_sheet_to_db, db)
    background_tasks.add_task(sync_db_to_sheet, db)
    return {"message": "Sync started in background"}