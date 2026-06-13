# CIM Equipment Integration Simulator 2.0

半導體設備 CIM 整合模擬系統 (Modern Web App 升級版)

## Project Overview
結合封測廠工作經驗與企業系統開發經驗，設計半導體設備資料上拋與 CIM Host 整合模擬系統。本專案展示「設備 → Host → Database → Dashboard / Notification」的完整資料流，並已升級為具備全端現代化架構的 Web App。

## Architecture
Equipment Simulator -> CIM Host API (FastAPI + WebSockets) -> PostgreSQL/SQLite -> React Dashboard (Vite) / Line Bot

## System Workflow (系統完整流程)

本系統模擬半導體工廠中設備與主機之間的資料交換邏輯，完整流程如下：

### 1. 設備初始化與註冊 (Registration Phase)
- **觸發時機**：模擬器啟動時。
- **動作**：10 台設備的模擬器執行緒啟動，並自動向 API 註冊至資料庫，同時同步最後已知的狀態 (State Synchronization) 避免重啟狀態遺失。

### 2. 週期性資料上拋與防呆生產 (Data Collection & Production Phase)
- **執行頻率**：每 **5 秒** 循環一次。
- **Lot 生產與防呆 (Recipe Mismatch)**：閒置 (`IDLE`) 的設備有小機率進貨並轉為 `RUN`。在此過程中有 10% 機率設備會帶錯配方，此時 Host 會觸發防呆阻擋，拋出 400 錯誤並發送 Line 告警。
- **感測器數據 (Sensor Data)**：模擬產生溫度與壓力數值並即時寫入資料庫。
- **異常發生 (Hardware Anomaly)**：運轉中設備有極小機率突發異常轉為 `DOWN` 或 `PM`。

### 3. Remote Command 交握 (Asynchronous Handshake)
- **遠端控制**：使用者從 Dashboard 對機台下發 `START`, `STOP`, `CHANGE_RECIPE`，API 將指令狀態設為 `PENDING`。
- **非同步處理**：對應的設備模擬器在輪詢中發現指令後，處理狀態轉換並回覆 `ACK/NACK`。
- **Simulator Power (模擬斷線互斥)**：若從儀表板將機台 Simulator Power 切換為 `Paused`，機台將不再處理指令，完美模擬設備斷線/關機時指令卡在 `PENDING` 的真實場景。

### 4. 異常監控與警報 (Alarm Handling Phase)
- **Alarm Rule Engine**：設備上拋感測器數據時，CIM Host API 會比對動態設定的規則庫。
- 若數值超標，由 API 自動建立警報，並透過 **Line Bot 主動告警**，將警報推播給系統管理者。

### 5. 零延遲現代化儀表板 (Modern React Dashboard)
- 拋棄傳統的輪詢閃爍介面，採用 **React 18 + Vite** 打造高質感玻璃擬物化 (Glassmorphism) 深色儀表板。
- 透過 **FastAPI WebSockets**，當機台狀態改變或指令交握完成時，後端主動推播 (Push) JSON 至前端，實現毫秒級的局部資料更新。

## Features
- **多設備模擬**: 支援 10 台設備 (ETCH, CVD, WET, PVD) 同步併發模擬。
- **CIM Host API**: 接收設備狀態、事件、Alarm、Sensor Data，並處理 Remote Command 交握。
- **Alarm Rule Engine**: 動態設定警報規則，觸發時主動建立異常。
- **防呆機制**: Recipe Mismatch 攔截邏輯與通知。
- **React + WebSocket 監控**: 現代化前端，無閃爍即時狀態推播。
- **Line Bot**: 支援對話互動查詢，並具備防呆與規則異常的主動推播功能。

## Tech Stack
- Python 3.10
- FastAPI + WebSockets
- React 18 + Vite (Vanilla CSS)
- PostgreSQL / SQLite (支援本地自動 Fallback)
- LINE Messaging API

## Quick Start

本專案提供 **Docker** 與 **本機手動** 兩種啟動方式供您選擇。

### 方式一：使用 Docker Compose 啟動 (推薦)
若您已安裝 Docker 與 Docker Compose，可直接在專案根目錄執行以下指令啟動資料庫與 API：
```bash
docker-compose up -d --build
```
> **Note**: 使用 Docker 啟動後，API 服務將自動運行於 `8000` port。接著請跳至下方執行**方式二**的第 2 步 (模擬器) 與第 3 步 (前端面板)。

### 方式二：純本機手動啟動

在啟動專案前，請開啟三個終端機 (Terminal) 分別啟動下列三個核心組件：

1. **啟動 CIM Host API (FastAPI 後台)**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. **啟動 設備模擬器 (Equipment Simulator)**
   （請確認 API 啟動完成後再執行）
   ```bash
   python simulator/equipment_simulator.py
   ```
3. **啟動 現代化監控面板 (React + Vite)**
   ```bash
   cd dashboard-react
   npm run dev
   ```

### 存取系統
待上述三個服務啟動完成後，您可透過瀏覽器前往：
- **現代化儀表板 (React)**: http://localhost:5173
- **API 文件 (Swagger)**: http://localhost:8000/docs
- **舊版靜態監控 (Streamlit)**: http://localhost:8501 (需另外手動執行 `streamlit run dashboard/streamlit_app.py`)

## Line Bot Setup (Webhook 整合)
要啟用 Line Bot 功能，請依照以下步驟設定：

1. 前往 **LINE Developers Console** 建立 Messaging API，取得 `Channel Secret` 與 `Channel Access Token`。
2. 開啟 `.env` 設定檔案，填入密鑰：
   ```env
   LINE_CHANNEL_ACCESS_TOKEN=您的Token
   LINE_CHANNEL_SECRET=您的Secret
   ```
3. 若在本機開發，請使用 `ngrok` 取得公開 HTTPS 網址：`ngrok http 8000`
4. 於 LINE Developers 後台將 Webhook URL 設定為：`https://<您的_ngrok_網址>/api/linebot/callback`
5. 啟用 Webhook 後即可透過 Line 查詢設備狀態或接收防呆警報。
