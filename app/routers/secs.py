from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import equipment as models
from app.schemas import equipment as schemas
import datetime

router = APIRouter()

@router.post("/message")
def receive_secs_message(msg_data: schemas.SecsMessageRequest, db: Session = Depends(get_db)):
    payload = {
        "event_id": msg_data.event_id,
        "report": msg_data.report
    }
    
    log = models.SecsMessageLog(
        eqp_id=msg_data.equipment_id,
        stream=msg_data.stream,
        function=msg_data.function,
        message_name=msg_data.message_name,
        direction=msg_data.direction,
        payload=payload,
        created_at=msg_data.event_time or datetime.datetime.now()
    )
    db.add(log)
    db.commit()
    return {"message": "SECS message processed"}

@router.get("/messages")
def get_secs_messages(limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.SecsMessageLog).order_by(models.SecsMessageLog.created_at.desc()).limit(limit).all()
