from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import datetime
import operator

from app.database import get_db
from app.models import equipment as models
from app.schemas import equipment as schemas
from app.routers.linebot import line_bot_api
from linebot.models import TextSendMessage
from app.ws_manager import manager

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
    manager.broadcast_sync({"type": "STATUS_UPDATE", "eqp_id": status_data.eqp_id})
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
    
    if alarm_data.alarm_status == "ACTIVE":
        try:
            msg = f"⚠️ [主動告警]\n設備: {alarm_data.eqp_id}\n代碼: {alarm_data.alarm_code}\n等級: {alarm_data.alarm_level}\n訊息: {alarm_data.alarm_message}"
            line_bot_api.broadcast(TextSendMessage(text=msg))
        except Exception as e:
            print(f"Line Bot broadcast failed: {e}")
            
    manager.broadcast_sync({"type": "ALARM_UPDATE", "eqp_id": alarm_data.eqp_id})

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
            
            try:
                msg = f"🚨 [規則告警]\n設備: {sensor_data.eqp_id}\n代碼: {rule.alarm_code}\n等級: {rule.alarm_level}\n訊息: {rule.alarm_message}\n觸發數值: {sensor_data.sensor_value}"
                line_bot_api.broadcast(TextSendMessage(text=msg))
            except Exception as e:
                print(f"Line Bot broadcast failed: {e}")
            manager.broadcast_sync({"type": "ALARM_UPDATE", "eqp_id": sensor_data.eqp_id})

    db.commit()
    return {"message": "Sensor data logged successfully"}

@router.get("/{eqp_id}/sensors")
def get_equipment_sensors(eqp_id: str, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.EquipmentSensorData).filter(models.EquipmentSensorData.eqp_id == eqp_id).order_by(models.EquipmentSensorData.collected_at.desc()).limit(limit).all()

@router.post("/{eqp_id}/remote-command")
def queue_remote_command(eqp_id: str, cmd_data: schemas.RemoteCommandCreate, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp_id).first()
    if not db_eqp:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    log = models.RemoteCommandLog(
        eqp_id=eqp_id,
        command_name=cmd_data.command_name,
        parameters=cmd_data.parameters,
        status="PENDING"
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    manager.broadcast_sync({"type": "COMMAND_UPDATE", "eqp_id": eqp_id})
    return {"message": "Command queued", "command_id": log.id, "status": "PENDING"}

@router.get("/{eqp_id}/commands")
def get_equipment_commands(eqp_id: str, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.RemoteCommandLog).filter(models.RemoteCommandLog.eqp_id == eqp_id).order_by(models.RemoteCommandLog.created_at.desc()).limit(limit).all()

@router.get("/{eqp_id}/commands/pending")
def get_pending_commands(eqp_id: str, db: Session = Depends(get_db)):
    return db.query(models.RemoteCommandLog).filter(models.RemoteCommandLog.eqp_id == eqp_id, models.RemoteCommandLog.status == "PENDING").all()

@router.post("/commands/{cmd_id}/reply")
def reply_command(cmd_id: int, reply_data: schemas.RemoteCommandReply, db: Session = Depends(get_db)):
    cmd = db.query(models.RemoteCommandLog).filter(models.RemoteCommandLog.id == cmd_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    
    cmd.status = reply_data.status
    cmd.updated_at = datetime.datetime.now()
    
    # 同步更新 Host 端的設備主檔狀態
    if reply_data.status == "ACK":
        db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == cmd.eqp_id).first()
        if db_eqp:
            if cmd.command_name == "CHANGE_RECIPE" and cmd.parameters and "recipe_id" in cmd.parameters:
                db_eqp.current_recipe_id = cmd.parameters["recipe_id"]
            elif cmd.command_name == "START":
                db_eqp.current_status = "RUN"
            elif cmd.command_name == "STOP":
                db_eqp.current_status = "IDLE"
                
    db.commit()
    manager.broadcast_sync({"type": "COMMAND_REPLY", "eqp_id": cmd.eqp_id})
    return {"message": "Command replied successfully"}

@router.post("/{eqp_id}/start")
def start_equipment(eqp_id: str, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp_id).first()
    if not db_eqp:
        raise HTTPException(status_code=404, detail="Equipment not found")
    db_eqp.enabled = True
    db.commit()
    return {"message": f"Equipment {eqp_id} simulation started"}

@router.post("/{eqp_id}/stop")
def stop_equipment(eqp_id: str, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp_id).first()
    if not db_eqp:
        raise HTTPException(status_code=404, detail="Equipment not found")
    db_eqp.enabled = False
    db.commit()
    return {"message": f"Equipment {eqp_id} simulation stopped"}

@router.post("/alarms/{alarm_id}/clear")
def clear_alarm(alarm_id: int, clear_data: schemas.AlarmClearRequest, db: Session = Depends(get_db)):
    db_alarm = db.query(models.EquipmentAlarmLog).filter(models.EquipmentAlarmLog.id == alarm_id).first()
    if not db_alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    
    db_alarm.alarm_status = "CLEARED"
    db_alarm.cleared_at = datetime.datetime.now()
    if clear_data.clear_message:
        db_alarm.alarm_message += f" [Cleared: {clear_data.clear_message}]"
    db.commit()
    return {"message": "Alarm cleared successfully"}

@router.post("/{eqp_id}/recipes/assign")
def assign_recipe(eqp_id: str, assign_data: schemas.RecipeAssignRequest, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp_id).first()
    if not db_eqp:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db_eqp.current_recipe_id = assign_data.recipe_id
    db.commit()
    return {"message": f"Recipe {assign_data.recipe_id} assigned to {eqp_id}"}

@router.post("/{eqp_id}/lots/{lot_id}/start")
def start_lot(lot_id: str, eqp_id: str, lot_data: schemas.LotStartRequest, db: Session = Depends(get_db)):
    db_eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp_id).first()
    if not db_eqp:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Check for Recipe Mismatch
    if lot_data.recipe_id and db_eqp.current_recipe_id and lot_data.recipe_id != db_eqp.current_recipe_id:
        alarm_log = models.EquipmentAlarmLog(
            eqp_id=eqp_id,
            alarm_code="RECIPE_MISMATCH",
            alarm_level="CRITICAL",
            alarm_message=f"Recipe mismatch: expected {db_eqp.current_recipe_id}, got {lot_data.recipe_id}",
            alarm_status="ACTIVE",
            occurred_at=datetime.datetime.now()
        )
        db.add(alarm_log)
        db.commit()
        try:
            msg = f"🚨 [防呆告警 - Recipe Mismatch]\n設備: {eqp_id}\nLot: {lot_id}\nHost配方: {db_eqp.current_recipe_id}\n設備回報配方: {lot_data.recipe_id}\n動作: 阻擋生產"
            line_bot_api.broadcast(TextSendMessage(text=msg))
        except Exception as e:
            pass
        raise HTTPException(status_code=400, detail="Recipe Mismatch! Production blocked.")
    
    db_eqp.current_lot_id = lot_id
    db_eqp.current_status = "RUN"
    db.commit()
    
    log = models.LotHistory(
        lot_id=lot_id,
        product_code=lot_data.product_code,
        route=lot_data.route,
        step_id=lot_data.step_id,
        quantity=lot_data.quantity,
        eqp_id=eqp_id,
        status="IN_PROGRESS",
        start_time=datetime.datetime.now()
    )
    db.add(log)
    db.commit()
    return {"message": f"Lot {lot_id} started on {eqp_id}"}
