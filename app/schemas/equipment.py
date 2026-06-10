from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

class EquipmentBase(BaseModel):
    eqp_id: str
    eqp_name: Optional[str] = None
    eqp_type: Optional[str] = None
    location: Optional[str] = None

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentResponse(EquipmentBase):
    id: int
    current_status: Optional[str] = None
    current_recipe_id: Optional[str] = None
    current_lot_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class EquipmentStatusCreate(BaseModel):
    eqp_id: str
    status: str
    previous_status: Optional[str] = None
    reason: Optional[str] = None
    event_time: Optional[datetime] = None

class EquipmentEventCreate(BaseModel):
    eqp_id: str
    event_id: str
    event_name: str
    payload: Optional[Dict[str, Any]] = None
    event_time: Optional[datetime] = None

class EquipmentAlarmCreate(BaseModel):
    eqp_id: str
    alarm_code: str
    alarm_level: str
    alarm_message: str
    alarm_status: str
    occurred_at: Optional[datetime] = None
    cleared_at: Optional[datetime] = None

class EquipmentSensorCreate(BaseModel):
    eqp_id: str
    sensor_name: str
    sensor_value: float
    unit: Optional[str] = None
    collected_at: Optional[datetime] = None

class RemoteCommandCreate(BaseModel):
    command_name: str
    parameters: Optional[Dict[str, Any]] = None

class SecsMessageRequest(BaseModel):
    stream: int
    function: int
    message_name: str
    equipment_id: str
    event_id: Optional[str] = None
    report: Optional[Dict[str, Any]] = None
    direction: Optional[str] = "EQP_TO_HOST"
    event_time: Optional[datetime] = None
