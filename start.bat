@echo off
TITLE CIM Equipment Integration Simulator - One-Click Start
CHCP 65001 > NUL
SETLOCAL

:: 檢查 .env 檔案
if not exist .env (
    echo [INFO] .env 檔案不存在，正在從 .env.example 複製...
    copy .env.example .env
)

echo ==========================================================
echo    CIM Equipment Integration Simulator 一鍵啟動腳本
echo ==========================================================
echo.
echo [1/3] 正在啟動 CIM Host API (FastAPI)...
start "CIM Host API" cmd /k "echo [CIM Host API] 啟動中... && uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: 等待 API 啟動
timeout /t 3 /nobreak > nul

echo [2/3] 正在啟動 Equipment Simulator (設備模擬器)...
start "Equipment Simulator" cmd /k "echo [Equipment Simulator] 啟動中... && python simulator/equipment_simulator.py"

echo [3/3] 正在啟動 Modern Dashboard (React + Vite)...
start "CIM Dashboard (React)" cmd /k "echo [React Dashboard] 啟動中... && cd dashboard-react && npm run dev -- --open"

echo.
echo ==========================================================
echo    啟動完畢！請查看各視窗輸出確認狀態。
echo ==========================================================
echo    API 文件 (Swagger): http://localhost:8000/docs
echo    現代化監控儀表板 (React): http://localhost:5173
echo ==========================================================
echo.
pause
