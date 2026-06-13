from fastapi import FastAPI
from app.routers import equipment, secs, linebot, rules
from app.database import engine, Base

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from app.ws_manager import manager

app = FastAPI(title="CIM Equipment Integration Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

app.include_router(equipment.router, prefix="/api/equipment", tags=["Equipment"])
app.include_router(rules.router, prefix="/api/rules", tags=["Alarm Rules"])
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
