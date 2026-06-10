from fastapi import FastAPI
from app.routers import equipment, secs, linebot
from app.database import engine, Base

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CIM Equipment Integration Simulator API")

app.include_router(equipment.router, prefix="/api/equipment", tags=["Equipment"])
app.include_router(secs.router, prefix="/api/secs", tags=["SECS"])
app.include_router(linebot.router, prefix="/api/linebot", tags=["Line Bot"])

# Simulator Control Logic
SIMULATOR_ENABLED = True

@app.get("/api/simulator/control")
def get_simulator_control():
    return {"enabled": SIMULATOR_ENABLED}

@app.post("/api/simulator/control")
def update_simulator_control(enabled: bool):
    global SIMULATOR_ENABLED
    SIMULATOR_ENABLED = enabled
    return {"enabled": SIMULATOR_ENABLED}

@app.get("/")
def root():
    return {"message": "Welcome to CIM Equipment Integration Simulator API"}
