from fastapi import APIRouter, Request, HTTPException, Depends
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from app.config import settings
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import equipment as models

router = APIRouter()

# Initialize Line Bot APIs
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

@router.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    body_str = body.decode('utf-8')
    
    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    reply_text = "我聽不懂這個指令，請嘗試輸入：\n- 查設備\n- 查設備 EQP-ETCH-001\n- 查異常\n- 查異常 EQP-ETCH-001\n- 查溫度 EQP-CVD-001"
    
    # 建立新的 DB Session 給 handler 使用
    db = SessionLocal()
    
    try:
        if text.startswith("查設備"):
            parts = text.split()
            if len(parts) > 1:
                eqp_id = parts[1]
                eqp = db.query(models.Equipment).filter(models.Equipment.eqp_id == eqp_id).first()
                if eqp:
                    reply_text = f"📌 設備 {eqp.eqp_id} ({eqp.eqp_name})\n狀態: {eqp.current_status}\n最後更新: {eqp.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
                else:
                    reply_text = f"找不到設備 {eqp_id}"
            else:
                eqps = db.query(models.Equipment).all()
                if eqps:
                    reply_text = "📌 目前設備清單：\n" + "\n".join([f"- {e.eqp_id}: {e.current_status}" for e in eqps])
                else:
                    reply_text = "目前無任何設備註冊。"
                
        elif text.startswith("查異常"):
            parts = text.split()
            if len(parts) > 1:
                eqp_id = parts[1]
                alarms = db.query(models.EquipmentAlarmLog).filter(models.EquipmentAlarmLog.eqp_id == eqp_id, models.EquipmentAlarmLog.alarm_status == 'ACTIVE').all()
            else:
                alarms = db.query(models.EquipmentAlarmLog).filter(models.EquipmentAlarmLog.alarm_status == 'ACTIVE').all()
            
            if alarms:
                reply_text = "⚠️ 目前未解除的警報：\n" + "\n".join([f"[{a.eqp_id}] {a.alarm_message}" for a in alarms])
            else:
                reply_text = "✅ 目前沒有任何未解除的警報！"
                
        elif text.startswith("查溫度"):
            parts = text.split()
            if len(parts) > 1:
                eqp_id = parts[1]
                sensor = db.query(models.EquipmentSensorData).filter(
                    models.EquipmentSensorData.eqp_id == eqp_id,
                    models.EquipmentSensorData.sensor_name == 'Temperature'
                ).order_by(models.EquipmentSensorData.collected_at.desc()).first()
                
                if sensor:
                    reply_text = f"🌡️ 設備 {eqp_id} 溫度: {sensor.sensor_value} {sensor.unit}"
                else:
                    reply_text = f"找不到設備 {eqp_id} 的溫度紀錄"
                    
    finally:
        db.close()

    # 回傳訊息給使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )
