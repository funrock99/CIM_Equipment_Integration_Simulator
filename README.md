# CIM Equipment Integration Simulator

半導體設備 CIM 整合模擬系統｜Side Project 求職展示版

## Project Overview
結合封測廠工作經驗與企業系統開發經驗，設計半導體設備資料上拋與 CIM Host 整合模擬系統。本專案為求職展示型 Side Project，展示「設備 → Host → Database → Dashboard / Notification」的完整資料流。

## Architecture
Equipment Simulator -> CIM Host API (FastAPI) -> PostgreSQL/SQLite -> Dashboard (Streamlit) / Line Bot

## System Workflow (系統完整流程)

本系統模擬半導體工廠中設備與主機之間的資料交換邏輯，完整流程如下：

### 1. 設備初始化與註冊 (Registration Phase)
- **觸發時機**：模擬器啟動時。
- **動作**：設備模擬器將預設的設備清單（如 Etcher, CVD 等）透過 API 註冊至資料庫。
- **目的**：建立基礎設備主檔，確保後續上拋資料能正確關聯。

### 2. 週期性資料上拋 (Data Collection Phase)
- **執行頻率**：每 **5 秒** 循環一次。
- **資料內容**：
    - **感測器數據 (Sensor Data)**：模擬產生溫度 (Temperature) 與壓力 (Pressure) 數值並即時寫入資料庫。
    - **設備狀態 (Status Change)**：每次循環有 20% 機率改變狀態 (RUN/IDLE/DOWN/PM)。
    - **SECS 訊息模擬**：狀態改變時同步產生 **S6F11 Event Report** 訊息 Log。

### 3. 異常監控與警報 (Alarm Handling Phase)
- **觸發條件**：當感測器數值異常（例如：溫度 > 85°C）。
- **動作**：
    - 立即產生 **S5F1 Alarm Report** 訊息。
    - 在資料庫 `equipment_alarm_log` 中標註為 `ACTIVE` 狀態。
- **目的**：模擬製造現場的異常即時回報機制。

### 4. 資料持久化與分析 (Persistence & Logic)
- **CIM Host API**：負責接收所有 POST 請求，驗證資料格式後透過 SQLAlchemy 寫入資料庫。
- **資料庫**：儲存所有歷史軌跡，包含狀態歷程、異常紀錄與 SECS 訊息原始 Payload。

### 5. 即時監控與互動 (Presentation & Interaction)
- **Dashboard**：定時向 API 抓取最新數據，以視覺化圖表展示設備稼動率與感測器趨勢。
- **Line Bot**：使用者可透過手機輸入指令查詢特定設備的最新狀態或異常清單。

## Features
- **Equipment Simulator**: 模擬多台封測/半導體設備定期上拋 RUN/IDLE/DOWN/PM 狀態與感測資料。
- **CIM Host API**: 接收設備狀態、事件、Alarm、Sensor Data 與 Remote Command。
- **SECS/GEM-style Message**: 模擬常見訊息流程如 S6F11 Event Report, S5F1 Alarm Report, S2F41 Remote Command。
- **Simulator Control Switch**: 支援從 Dashboard 遠端開啟/關閉模擬器上拋，便於展示並大幅降低雲端部署成本。
- **Dashboard**: Streamlit 建立的設備狀態監控、Alarm 清單、Sensor 趨勢。
- **Line Bot**: 即時查詢設備狀態、異常報警與最新溫度感測數據。

## Tech Stack
- Python 3.10
- FastAPI
- PostgreSQL / SQLAlchemy
- Streamlit
- Docker Compose

## Quick Start

### Windows One-Click Start
如果你是在 Windows 環境下，可以直接執行根目錄的批次檔：
```bash
start.bat
```
這會自動啟動 API、模擬器與監控儀表板。

### 手動啟動步驟
1. Start database and API with Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

2. Start Equipment Simulator:
   ```bash
   pip install requests
   python simulator/equipment_simulator.py
   ```

3. Start Dashboard:
   ```bash
   pip install streamlit pandas
   streamlit run dashboard/streamlit_app.py
   ```

4. API Documentation:
   http://localhost:8000/docs

## Environment Setup (環境變數設定)

在啟動專案前，請先建立環境變數設定檔：

1. 複製環境變數範例檔，於專案根目錄建立 `.env` 檔案：
   - Windows (PowerShell / 命令提示字元):
     ```cmd
     copy .env.example .env
     ```
   - Linux / macOS / Git Bash:
     ```bash
     cp .env.example .env
     ```
2. （選用）開啟 `.env`，可根據您的環境調整資料庫連線等設定（預設為 SQLite 可直接啟動）。

## Line Bot Setup (Webhook 整合)
要啟用 Line Bot 功能，請依照以下步驟設定：

1. 前往 **LINE Developers Console** 建立 Messaging API，取得 `Channel Secret` 與 `Channel Access Token`。
2. 開啟剛剛建立的 `.env` 設定檔案，填入您的 Line Bot 密鑰：
   ```env
   LINE_CHANNEL_ACCESS_TOKEN=您的Token
   LINE_CHANNEL_SECRET=您的Secret
   ```
3. 若在本機開發，請使用 `ngrok` 取得公開 HTTPS 網址：
   ```bash
   ngrok http 8000
   ```
4. 於 LINE Developers 後台將 Webhook URL 設定為：`https://<您的_ngrok_網址>/api/linebot/callback`
5. 啟用 Webhook 功能後即可向 Bot 傳送指令（例如：「查設備」、「查異常」、「查溫度 EQP-ETCH-001」）進行互動查詢。
