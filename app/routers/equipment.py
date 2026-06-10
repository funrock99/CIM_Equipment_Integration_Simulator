from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import datetime
import operator

from app.database import get_db
from app.models import equipment as models
from app.schemas import equipment as schemas

router = APIRouter()

@router.post("/register", response_model=schemas.EquipmentResponse)
def register_equipment(eqp: schemas.EquipmentCreate, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp.eqp_id).first()
    if db_eqp:
        raise HTTPException(status_code=400, detail="Equipment already registered")
    
    new_eqp = models.Equipment(
        eqp_id=eqp.eqp_id,
        eqp_name=eqp.eqp_name,
        eqp_type=eqp.eqp_type,
        location=eqp.location,
        current_status="IDLE"
    )
    db.add(new_eqp)
    db.commit()
    db.refresh(new_eqp)
    return new_eqp

@router.get("", response_model=List[schemas.EquipmentResponse])
def get_all_equipment(db: Session = Depends(get_db)):
    return db.query(models.Equipment).all()

# ================= Alarm Rules =================
@router.post("/rules", response_model=schemas.AlarmRuleResponse)
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

@router.get("/rules", response_model=List[schemas.AlarmRuleResponse])
def get_alarm_rules(db: Session = Depends(get_db)):
    return db.query(models.AlarmRule).all()

@router.delete("/rules/{rule_id}")
def delete_alarm_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(models.AlarmRule).filter(models.AlarmRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted successfully"}

# ================= Equipment Operations =================
@router.get("/{eqp_id}", response_model=schemas.EquipmentResponse)
def get_equipment(eqp_id: str, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp_id).first()
    if not db_eqp:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return db_eqp

@router.post("/status")
def report_status(status_data: schemas.EquipmentStatusCreate, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == status_data.eqp_id).first()
    if not db_eqp:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db_eqp.current_status = status_data.status
    db_eqp.updated_at = datetime.datetime.now()
    
    log = models.EquipmentStatusLog(
        eqp_id=status_data.eqp_id,
        status=status_data.status,
        previous_status=status_data.previous_status,
        reason=status_data.reason,
        event_time=status_data.event_time or datetime.datetime.now()
    )
    db.add(log)
    db.commit()
    return {"message": "Status updated successfully"}

@router.get("/{eqp_id}/status")
def get_equipment_status(eqp_id: str, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp_id).first()
    if not db_eqp:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return {"eqp_id": eqp_id, "current_status": db_eqp.current_status, "updated_at": db_eqp.updated_at}

@router.post("/event")
def report_event(event_data: schemas.EquipmentEventCreate, db: Session = Depends(get_db)):
    log = models.EquipmentEventLog(
        eqp_id=event_data.eqp_id,
        event_id=event_data.event_id,
        event_name=event_data.event_name,
        payload=event_data.payload,
        event_time=event_data.event_time or datetime.datetime.now()
    )
    db.add(log)
    db.commit()
    return {"message": "Event logged successfully"}

@router.get("/{eqp_id}/events")
def get_equipment_events(eqp_id: str, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.EquipmentEventLog).filter(models.EquipmentEventLog.eqp_id == eqp_id).order_by(models.EquipmentEventLog.event_time.desc()).limit(limit).all()

@router.post("/alarm")
def report_alarm(alarm_data: schemas.EquipmentAlarmCreate, db: Session = Depends(get_db)):
    log = models.EquipmentAlarmLog(
        eqp_id=alarm_data.eqp_id,
        alarm_code=alarm_data.alarm_code,
        alarm_level=alarm_data.alarm_level,
        alarm_message=alarm_data.alarm_message,
        alarm_status=alarm_data.alarm_status,
        occurred_at=alarm_data.occurred_at or datetime.datetime.now(),
        cleared_at=alarm_data.cleared_at
    )
    db.add(log)
    db.commit()
    return {"message": "Alarm logged successfully"}

@router.get("/{eqp_id}/alarms")
def get_equipment_alarms(eqp_id: str, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.EquipmentAlarmLog).filter(models.EquipmentAlarmLog.eqp_id == eqp_id).order_by(models.EquipmentAlarmLog.occurred_at.desc()).limit(limit).all()

@router.post("/sensor")
def report_sensor(sensor_data: schemas.EquipmentSensorCreate, db: Session = Depends(get_db)):
    log = models.EquipmentSensorData(
        eqp_id=sensor_data.eqp_id,
        sensor_name=sensor_data.sensor_name,
        sensor_value=sensor_data.sensor_value,
        unit=sensor_data.unit,
        collected_at=sensor_data.collected_at or datetime.datetime.now()
    )
    db.add(log)
    
    # 檢查是否觸發 Alarm Rule
    rules = db.query(models.AlarmRule).filter(models.AlarmRule.sensor_name == sensor_data.sensor_name).all()
    for rule in rules:
        if rule.eqp_id and rule.eqp_id != sensor_data.eqp_id:
            continue
            
        ops = {'>': operator.gt, '<': operator.lt, '>=': operator.ge, '<=': operator.le, '==': operator.eq, '!=': operator.ne}
        op_func = ops.get(rule.condition)
        if op_func and op_func(float(sensor_data.sensor_value), float(rule.threshold_value)):
            alarm_log = models.EquipmentAlarmLog(
                eqp_id=sensor_data.eqp_id,
                alarm_code=rule.alarm_code,
                alarm_level=rule.alarm_level,
                alarm_message=f"{rule.alarm_message} (Value: {sensor_data.sensor_value})",
                alarm_status="ACTIVE",
                occurred_at=datetime.datetime.now()
            )
            db.add(alarm_log)
            # 此處可未來擴充：呼叫 Line Bot API 推播

    db.commit()
    return {"message": "Sensor data logged successfully"}

@router.get("/{eqp_id}/sensors")
def get_equipment_sensors(eqp_id: str, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.EquipmentSensorData).filter(models.EquipmentSensorData.eqp_id == eqp_id).order_by(models.EquipmentSensorData.collected_at.desc()).limit(limit).all()

@router.post("/{eqp_id}/remote-command")
def send_remote_command(eqp_id: str, cmd_data: schemas.RemoteCommandCreate, db: Session = Depends(get_db)):
    log = models.RemoteCommandLog(
        eqp_id=eqp_id,
        command_name=cmd_data.command_name,
        parameters=cmd_data.parameters,
        status="PENDING"
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"message": "Command queued", "command_id": log.id, "status": "PENDING"}

@router.get("/{eqp_id}/commands")
def get_equipment_commands(eqp_id: str, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.RemoteCommandLog).filter(models.RemoteCommandLog.eqp_id == eqp_id).order_by(models.RemoteCommandLog.created_at.desc()).limit(limit).all()


