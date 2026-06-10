from sqlalchemy import Column, Integer, String, Numeric, Text, TIMESTAMP, text, JSON
from app.database import Base

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50), unique=True, nullable=False, index=True)
    eqp_name = Column(String(100))
    eqp_type = Column(String(50))
    location = Column(String(100))
    current_status = Column(String(30))
    current_recipe_id = Column(String(50))
    current_lot_id = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class EquipmentStatusLog(Base):
    __tablename__ = "equipment_status_log"

    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50), nullable=False)
    status = Column(String(30))
    previous_status = Column(String(30))
    reason = Column(Text)
    event_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class EquipmentEventLog(Base):
    __tablename__ = "equipment_event_log"
    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50), nullable=False)
    event_id = Column(String(50))
    event_name = Column(String(100))
    payload = Column(JSON)
    event_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class EquipmentAlarmLog(Base):
    __tablename__ = "equipment_alarm_log"
    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50), nullable=False)
    alarm_code = Column(String(50))
    alarm_level = Column(String(20))
    alarm_message = Column(Text)
    alarm_status = Column(String(20))
    occurred_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    cleared_at = Column(TIMESTAMP)

class EquipmentSensorData(Base):
    __tablename__ = "equipment_sensor_data"
    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50), nullable=False)
    sensor_name = Column(String(50))
    sensor_value = Column(Numeric)
    unit = Column(String(20))
    collected_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class RemoteCommandLog(Base):
    __tablename__ = "remote_command_log"
    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50), nullable=False)
    command_name = Column(String(50))
    parameters = Column(JSON)
    status = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class SecsMessageLog(Base):
    __tablename__ = "secs_message_log"
    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50))
    stream = Column(Integer)
    function = Column(Integer)
    message_name = Column(String(100))
    direction = Column(String(20))
    payload = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
