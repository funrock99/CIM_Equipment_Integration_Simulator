from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import equipment as models
from app.schemas import equipment as schemas

router = APIRouter()

@router.post("", response_model=schemas.AlarmRuleResponse)
def create_alarm_rule(rule_data: schemas.AlarmRuleCreate, db: Session = Depends(get_db)):
    new_rule = models.AlarmRule(
        eqp_id=rule_data.eqp_id,
        sensor_name=rule_data.sensor_name,
        condition=rule_data.condition,
        threshold_value=rule_data.threshold_value,
        alarm_code=rule_data.alarm_code,
        alarm_level=rule_data.alarm_level,
        alarm_message=rule_data.alarm_message
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@router.get("", response_model=List[schemas.AlarmRuleResponse])
def get_alarm_rules(db: Session = Depends(get_db)):
    return db.query(models.AlarmRule).all()

@router.delete("/{rule_id}")
def delete_alarm_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(models.AlarmRule).filter(models.AlarmRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted successfully"}
