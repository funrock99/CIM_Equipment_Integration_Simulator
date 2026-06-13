from sqlalchemy import Column, Integer, String, Numeric, Text, TIMESTAMP, text, JSON, Boolean
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
    enabled = Column(Boolean, default=True)
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

class AlarmRule(Base):
    __tablename__ = "alarm_rule"
    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50), nullable=True, index=True) # None means applies to all
    sensor_name = Column(String(50), nullable=False)
    condition = Column(String(10), nullable=False) # '>', '<', '==', '>=', '<='
    threshold_value = Column(Numeric, nullable=False)
    alarm_code = Column(String(50), nullable=False)
    alarm_level = Column(String(20), nullable=False)
    alarm_message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class RecipeMaster(Base):
    __tablename__ = "recipe_master"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(String(50), unique=True, nullable=False, index=True)
    recipe_name = Column(String(100))
    version = Column(String(20))
    equipment_type = Column(String(50))
    parameter_json = Column(JSON)
    status = Column(String(20)) # e.g. ACTIVE, DRAFT, OBSOLETE
    updated_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class RecipeHistory(Base):
    __tablename__ = "recipe_history"
    id = Column(Integer, primary_key=True, index=True)
    eqp_id = Column(String(50), nullable=False)
    recipe_id = Column(String(50))
    version = Column(String(20))
    action = Column(String(50)) # e.g. ASSIGNED, MISMATCHED
    performed_by = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class LotHistory(Base):
    __tablename__ = "lot_history"
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(String(50), nullable=False, index=True)
    product_code = Column(String(50))
    route = Column(String(50))
    step_id = Column(String(50))
    quantity = Column(Integer)
    eqp_id = Column(String(50))
    status = Column(String(20)) # e.g. CREATED, IN_PROGRESS, COMPLETED, ABORTED
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

class UserAccount(Base):
    __tablename__ = "user_account"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(50), nullable=False)
    password_hash = Column(String(255))
    role = Column(String(20)) # e.g. Admin, Engineer, Operator, Viewer
    enabled = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

