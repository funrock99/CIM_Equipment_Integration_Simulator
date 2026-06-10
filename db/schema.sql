CREATE TABLE equipment (
    id SERIAL PRIMARY KEY,
    eqp_id VARCHAR(50) UNIQUE NOT NULL,
    eqp_name VARCHAR(100),
    eqp_type VARCHAR(50),
    location VARCHAR(100),
    current_status VARCHAR(30),
    current_recipe_id VARCHAR(50),
    current_lot_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE equipment_alarm_log (
    id SERIAL PRIMARY KEY,
    eqp_id VARCHAR(50) NOT NULL,
    alarm_code VARCHAR(50),
    alarm_level VARCHAR(20),
    alarm_message TEXT,
    alarm_status VARCHAR(20),
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cleared_at TIMESTAMP
);

CREATE TABLE equipment_sensor_data (
    id SERIAL PRIMARY KEY,
    eqp_id VARCHAR(50) NOT NULL,
    sensor_name VARCHAR(50),
    sensor_value NUMERIC,
    unit VARCHAR(20),
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE secs_message_log (
    id SERIAL PRIMARY KEY,
    eqp_id VARCHAR(50),
    stream INTEGER,
    function INTEGER,
    message_name VARCHAR(100),
    direction VARCHAR(20),
    payload JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE equipment_status_log (
    id SERIAL PRIMARY KEY,
    eqp_id VARCHAR(50) NOT NULL,
    status VARCHAR(30),
    previous_status VARCHAR(30),
    reason TEXT,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE equipment_event_log (
    id SERIAL PRIMARY KEY,
    eqp_id VARCHAR(50) NOT NULL,
    event_id VARCHAR(50),
    event_name VARCHAR(100),
    payload JSONB,
    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE remote_command_log (
    id SERIAL PRIMARY KEY,
    eqp_id VARCHAR(50) NOT NULL,
    command_name VARCHAR(50),
    parameters JSONB,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
