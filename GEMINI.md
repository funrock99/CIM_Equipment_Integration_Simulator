## Agent 執行規範 (Hermes & Karpathy 核心機制)

### 1. 工作記憶 (Working Memory) - 思考與進度
- **任務初始化**：在執行任何修改前，必須先輸出 `## 任務狀態追蹤` 塊。
- **追蹤內容**：明確定義 [目標]、[當前子任務]、[假設與驗證方法]。
- **Surgical Edits**：僅觸動必要的代碼，嚴格保持現有的 GUI/CLI 雙重架構與縮排風格。

### 2. 三層記憶應用 (Memory System)
- **Working**：透過 `## 任務狀態追蹤` 維持短期邏輯連貫。
- **Long-term**：解決複雜 Bug 或新增核心功能後，需自動更新「近期紀錄」中的「技術要點」，將經驗固化。

### 3. 自改進循環 (Self-improving Loop) - 驗證與反思
- **執行後驗證**：修改代碼後，必須嘗試執行（例如使用 `--help` 或空運行測試），確保腳本可正常啟動。
- **反思 (Reflect)**：若任務失敗，需分析原因（如網路超時、反爬蟲升級）並記錄在記憶中，避免重複錯誤。

---

## 📈 近期紀錄 (Technical Notes)

- 排序規則：`Technical Notes` 採 `DESC`，最新紀錄固定放在最上方。

- **[2026-06-14] 重構 React 儀表板架構 (復刻 Streamlit Sidebar)、補齊警報與圖表、以及全面容器化 (Docker)**
  - **核心功能**：為了解決先前由 Streamlit 轉換至 React 時遺失的「警報紀錄」、「規則引擎管理」與「感測器趨勢圖 (Sensor Trends)」等功能，對 `App.jsx` 進行了全面的結構重構。引入側邊欄 (Sidebar) 分頁設計以完美還原原先的操作手感，並加入前端分頁 (Pagination) 機制優化 Alarm Logs 顯示。
  - **技術要點 (Refactoring & Architecture)**：
    - **Recharts 圖表整合**：使用 `recharts` 實作動態感測器數值折線圖，解決了原本 Streamlit 才有圖表的問題，並搭配 Glassmorphism 風格調整 Tooltip 與配色。
    - **WebSocket Alarm 即時推播**：在 FastAPI 的 `report_sensor` 與 `report_alarm` 路由中，新增 `manager.broadcast_sync({"type": "ALARM_UPDATE"})`，讓前端不需重整即可即時浮現因規則觸發的新警報。
    - **全面容器化 (Docker Compose All-in-One)**：重寫 `docker-compose.yml` 並為 `dashboard-react` 撰寫專屬 `Dockerfile` (基於 `node:18-alpine`)。修復了設備模擬器硬編碼 `localhost` 的連線問題，改為透過 `API_URL` 環境變數自適應 Docker 內部網路，達成前端、API、資料庫、模擬器的一鍵佈署。
    - **排版優化 (Flexbox)**：精確修復 `select`、`input` 與 `button` 在 HTML 盒模型中高度不一致的排版痛點，透過統一設定 `height: 42px; box-sizing: border-box;` 與 `flex` 容器完美對齊表單元件。
  - **後續步驟**：擴充 Dashboard 以支援更進階的 OEE 計算或開始設計 AI Anomaly Detection 模型介面。

- **[2026-06-14] 導入 React + Vite 與 WebSocket 打造現代化零延遲 Dashboard**
  - **核心功能**：為解決 Streamlit 定期重整造成的畫面閃爍 (Flickering) 與閱讀干擾，徹底升級前端架構，改以 React 打造具備 Glassmorphism 科技感的 Web App，並透過 WebSocket 實現機台狀態與遠端指令交握的即時推播。
  - **技術要點 (Bug Fix & Architecture)**：
    - **WebSocket Push**：於 FastAPI 實作 `ConnectionManager`，當 `current_status` 變更或 Remote Command 收到 `ACK` 時主動廣播 JSON。
    - **Stale Closure 修復**：解決 React `useEffect` 內 WebSocket 監聽器造成的過期閉包陷阱，透過 `setSelectedEqp(prev => ...)` 函數式更新避免狀態回彈。
    - **Timezone 校正**：修復 SQLite `CURRENT_TIMESTAMP` (UTC) 傳至前端時被錯誤解讀為 Local Time 的 Bug，強制附加 `'Z'` 使 JavaScript 正確轉換為當地時區 (+8)。
    - **Simulator State Synchronization**：修復模擬器重啟時初始狀態被硬編碼重置為 `IDLE` 的 Bug，改為啟動時主動向 Host 查詢最後狀態；並修正隨機狀態切換邏輯，確保 `STOP` 指令能正確維持機台閒置。
  - **後續步驟**：擴充 Dashboard 以支援更進階的 OEE 計算或開始設計 AI Anomaly Detection 模型介面。

- **[2026-06-13] 實作 Remote Command (ACK/NACK) 與 Recipe Mismatch 防呆阻擋機制**
  - **核心功能**：讓設備模擬器具備接收 Host 遠端指令 (START, STOP, CHANGE_RECIPE) 並回應 ACK/NACK 的能力。此外，於 Lot 開始生產時進行防呆比對，當實體配方與 Host 派發配方不符時，主動阻擋並發送 Line 告警。
  - **技術要點**：
    - **Remote Command**：在 Dashboard 開發送出指令的介面，CIM Host API 將指令設定為 `PENDING`。設備模擬器每次輪詢 `GET /commands/pending`，解析參數後將狀態轉換，並回覆 `/commands/{cmd_id}/reply` 完成交握。
    - **Recipe Mismatch**：`POST /lots/{lot_id}/start` API 加入比對邏輯，當設備模擬器有 10% 的機率模擬帶錯配方 (`-WRONG`) 進行生產時，拋出 HTTPException(400)，並將錯誤事件寫入 Alarm 資料表及透過 `line_bot_api` 廣播 `[防呆告警]` 給負責人。
  - **後續步驟**：擴充 Dashboard 以支援更進階的 OEE 計算或開始設計 AI Anomaly Detection 模型介面。

- **[2026-06-11] 實作監控項目「Line主動告警」**
  - **核心功能**：當 CIM Host API 端接收到設備主動上報或經由規則引擎觸發的 Alarm 時，自動推播警報訊息至 Line。
  - **技術要點**：修改 `app/routers/equipment.py`，在 `report_alarm` 與 `report_sensor` API 處理邏輯中導入 `line_bot_api.broadcast()`，將設備 ID、警報代碼與異常數值即時推播給系統管理者。
  - **後續步驟**：擴展 Line Bot 以記錄特定的使用者 ID，以支援更精準的分眾或個人化訂閱推播，取代全域廣播。

- **[2026-06-11] Alarm Rule 架構重構與圖形化管理面板實作**
  - **核心功能**：在 Streamlit Dashboard 中實作專屬的管理介面，讓使用者可直覺地新增與刪除警報邏輯。
  - **技術要點 (Bug Fix & Refactoring)**：
    - 解決了 FastAPI 路由衝突 Bug：由於 `GET /{eqp_id}` 會攔截 `GET /rules`，導致介面收到 404 錯誤。
    - 實施 RESTful 架構優化，將警報規則從設備路由中抽離，獨立建立 `app/routers/rules.py` 作為系統層級的全局端點 (`/api/rules`)。
  - **後續步驟**：實作當 API 端觸發 Alarm 時，主動呼叫 Line Bot 進行訊息推播。

- **[2026-06-11] 實作動態警報規則引擎 (Alarm Rule Engine)**
  - **核心功能**：讓 CIM Host API 具備規則判斷能力，拔除設備模擬器中硬編碼的 Alarm 觸發邏輯。
  - **技術要點**：
    - 新增 `AlarmRule` 資料表與 API 端點 (`/api/rules`) 提供動態增刪查改警報規則。
    - 於 API 接收 Sensor Data 時，動態讀取規則比對數值，若超標則由 API 端自動生成對應的 Alarm 事件。
    - 設備模擬器啟動時，會自動註冊一筆預設規則 (Temperature > 85.0)。
  - **後續步驟**：實作當 API 端觸發 Alarm 時，主動呼叫 Line Bot 進行訊息推播。

- **[2026-06-09] 實作模擬器遠端開關機制 (Simulator Control Switch)**
  - **核心功能**：在 Dashboard 側邊欄新增切換開關，可遠端暫停/恢復模擬器的資料上拋。
  - **技術要點**：
    - **API 驅動狀態管理**：在 FastAPI 實作控制端點，模擬器在每 5 秒的迴圈中主動輪詢 (Polling) 該狀態。
    - **雲端成本優化**：此設計允許系統在部署於 GCP 時，平時維持靜默狀態以節省資料庫 IO 與流量費用，僅在 Demo 時開啟。
    - **非侵入式控制**：模擬器被暫停時僅跳過該次循環，不影響已註冊的設備狀態與連線。

- **[2026-06-09] 新增 Windows 一鍵啟動腳本 (start.bat) 與 環境優化**
  - **核心功能**：建立 `start.bat` 批次檔，整合 FastAPI、Simulator 與 Dashboard 啟動流程。
  - **技術要點**：修正 `.env` 預設值，將 `DATABASE_URL` 改為 SQLite 以支援無 Docker 環境的即時啟動。解決了因 PostgreSQL 連線失敗導致 API 無法啟動的 Bug。
  - **後續步驟**：持續優化 Simulator 穩定性。

- **[2026-06-04] Line Bot 串接實作與 GCP 部署架構確立**
  - **核心功能**：使用 `line-bot-sdk` 實作 Line Webhook 端點 (`/api/linebot/callback`)，支援「查設備」、「查異常」、「查溫度」等即時狀態互動查詢。
  - **技術要點 (Cloud Ready)**：確認專案具備 12-Factor App 特性，透過 SQLAlchemy `Base.metadata.create_all` 實現雲端部署時的資料表自動生成機制。系統能依據 `DATABASE_URL` 環境變數，無縫在本地 SQLite 與 GCP Cloud SQL (PostgreSQL) 之間自動切換，達到「零改 Code 部署」的目標。
  - **後續步驟**：擴充 Alarm Rule Engine 以支援異常發生時的主動 Line 推播通知。

- **[2026-06-04] CIM Equipment Integration Simulator MVP 開發與本地相容性優化**
  - **核心功能**：完成基於 FastAPI 的 CIM Host API、Python 設備模擬器 (Equipment Simulator)、Streamlit Dashboard 監控儀表板。
  - **技術要點 (SQLite Fallback)**：因應無 Docker 測試環境，將 `config.py` 中的資料庫連線設為可自動 fallback 至 `sqlite:///./cim.db`，並將資料庫模型 (`app/models/equipment.py`) 的 `JSONB` 修改為跨資料庫通用的 `JSON`，確保系統完全支援無 Docker 的本地直接啟動。
  - **後續步驟**：擴充 Alarm Rule Engine、支援 Line Bot 查詢與推播功能。
