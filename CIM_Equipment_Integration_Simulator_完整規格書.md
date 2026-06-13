**CIM Equipment Integration Simulator 2.0  
完整系統規格書 (Software Specification Document)**

半導體設備 CIM 整合模擬系統｜Side Project 求職展示版

| **文件項目** | **內容**                                                                                   |
|--------------|--------------------------------------------------------------------------------------------|
| 專案名稱     | CIM Equipment Integration Simulator 2.0                                                    |
| 中文名稱     | 半導體設備 CIM 整合模擬系統                                                                |
| 目標職務     | CIM / MES / EAP / SECS-GEM / 製造資訊系統 / 系統整合工程師 / AIOps 工程師                  |
| 技術主軸     | Python FastAPI、WebSockets、React (Vite)、PostgreSQL、SECS/GEM 模擬、Line Bot、Docker      |
| 使用情境     | 封測廠 / 半導體製造現場設備資料上拋、異常回報、Remote Command、即時查詢、預知保養擴充基礎 |
| 文件版本     | v2.1 (優化升級版)                                                                           |
| 設計方法     | Spec-Driven Development (SDD)                                                              |

---

# 1. 專案背景與定位

本專案為求職展示型 Side Project，目的是將封測廠經驗與長期企業系統開發經驗結合，建立一套模擬半導體設備與 CIM Host 資料交換的系統。專案重點不僅是單純 CRUD，而是展示「設備 → Host → Database → Dashboard / Notification」的完整資料流。

2.0 版本經過優化升級，已具備以下現代化與進階功能：
- **動態告警規則引擎 (Alarm Rule Engine)** 取代隨機告警，根據 Sensor 數據動態判斷異常。
- **Recipe Mismatch 防呆阻擋機制**：Host 端阻擋設備的錯誤配方並推播通知。
- **Remote Command (ACK/NACK)**：完整的遠端指令交握非同步流程。
- **現代化 WebSocket 即時推播**：以 React + Vite 打造零延遲、無閃爍的現代化前端介面。

| **角色定位**       | **說明**                                                                |
|--------------------|-------------------------------------------------------------------------|
| 不是初階轉職者     | 已有封測廠場域經驗，理解製造現場、設備狀態、異常與跨部門溝通情境。      |
| 不是單純後端工程師 | 專案涵蓋設備模擬、SECS/GEM 訊息、狀態機、資料流、監控與通知。         |
| 主打系統整合能力   | 具備從底層 Python 模擬器、FastAPI 後端、到現代化 React 前端的全端整合能力。 |

---

# 2. 專案目標與非目標 (Goals and Non-Goals)

## 2.1 專案目標 (Goals)
1. 建立可展示 CIM / MES / EAP 整合能力的模擬平台。
2. 模擬 10 台設備上拋資料與 Host 指令下發 (START/STOP/CHANGE_RECIPE) 交握流程。
3. 提供具備 WebSocket 即時資料推播的 React Dashboard 與 Line Bot 主動推播。
4. 實作真實工廠的防呆邏輯 (Recipe Mismatch) 與動態告警判定。
5. 作為 Predictive Maintenance / AIOps 模組的基礎平台。

## 2.2 非目標 (Non-Goals)
- 不追求真實機台通訊 stack (如 HSMS binary protocol) 的完整實作。
- 不以工廠正式上線系統為目標，不實作生產等級 HA / Cluster。
- 不以訓練大型 AI 模型為第一優先。

---

# 3. 系統範圍 (Scope)

## 3.1 包含範圍 (In Scope)
1. **多設備擴充**：支援 10 台設備 (ETCH, CVD, WET, PVD) 同步並發模擬，並支援單機獨立啟停控制。
2. **設備狀態機**：RUN, IDLE, DOWN, PM 等狀態流轉。
3. **動態告警引擎 (Alarm Rule Engine)**：API 端動態判斷數值超標並產生告警。
4. **防呆阻擋 (Recipe Mismatch)**：攔截設備攜帶錯誤配方的生產請求。
5. **Remote Command 模擬**：Host 下發 START/STOP/CHANGE_RECIPE，並處理 ACK/NACK 與狀態同步。
6. **Lot 流程模擬**：Lot 建立、隨機批次開始與結束。
7. **Sensor Data 模擬**：連續型感測器數據與異常 Spike。
8. **現代化 Dashboard**：基於 React + WebSocket 的即時設備總覽與指令歷程。
9. **Notification / Line Bot**：LINE 異常主動通知 (規則告警、防呆告警) 與互動查詢。
10. **Docker 化部署**：一鍵啟動本地環境。

## 3.2 不包含範圍 (Out of Scope)
- 真實設備連線與實際 MES 正式整合。
- 完整前後台多租戶 SaaS 管理。

---

# 4. 使用者角色與利益關係人 (Stakeholders)

| **角色**        | **權限 / 需求**                                           | **系統功能 / 說明**                               |
|-----------------|-----------------------------------------------------------|---------------------------------------------------|
| Admin           | 管理設備、Recipe、使用者權限                              | 全域管理，系統開發者與維護者。                    |
| Engineer        | 下發 Remote Command、追蹤 Alarm 與 Sensor 趨勢            | Dashboard Alarm 清單、Sensor 圖表、Command API。  |
| Operator        | 查詢設備狀態與 Lot、確認資料上拋是否正常                  | Line Bot 查設備、Dashboard 設備總覽。             |
| Hiring Manager  | 評估作品與技術能力                                        | 現代化 React UI 展示、完整架構圖、Demo Script。   |

---

# 5. 整體系統架構與資料流

## 5.1 系統架構圖

```text
+-------------------------+  
| Equipment Simulator     |  
| (模擬 10台機台併發)       |  
+------------+------------+  
             | HTTP POST (Status, Sensor, Command Polling, Lot Start)  
             v  
+-------------------------+  
| CIM Host API            |  <-----> +--------------------+
| (FastAPI + WebSockets)  |  Push    | React (Vite)       |
+------------+------------+  Events  | Dashboard          |
             | SQLAlchemy            +--------------------+
             v  
+-------------------------+          +--------------------+
| SQLite / PostgreSQL     |          | Line Bot           |
| (設備, 歷程, 告警, 規則)| -------->| (即時查詢/防呆推播)|
+-------------------------+          +--------------------+
```

## 5.2 邏輯元件 (Logical Components)
1. **API Gateway Layer**：FastAPI 提供 REST 端點與 WebSocket 管理器。
2. **Equipment Simulation Engine**：獨立 Thread 模擬多台設備行為。
3. **Alarm Rule Engine**：接收 Sensor 資料並動態比對規則庫，產生告警。
4. **Prevention Engine (防呆)**：於 Lot Start 階段攔截 Mismatch 配方。
5. **Persistence Layer**：SQLAlchemy ORM 存取資料庫。
6. **Frontend Dashboard**：React + Vite 即時互動介面。
7. **Notification Adapter**：LINE Bot API 串接。

---

# 6. 技術架構與工具

| **類別**  | **技術**                  | **用途**                                           |
|-----------|---------------------------|----------------------------------------------------|
| 後端      | Python FastAPI            | CIM Host API、WebSockets 推播管理。                |
| 前端      | React 18 + Vite           | 打造高質感、零延遲、無閃爍的現代化監控面板。       |
| ORM       | SQLAlchemy                | 資料庫模型與 CRUD 操作。                           |
| 資料庫    | SQLite / PostgreSQL       | 開發期自動 Fallback SQLite，上雲端時切換 PostgreSQL|
| 即時通訊  | WebSockets                | 設備狀態變更與指令交握時的即時 UI 推播更新。       |
| 通知查詢  | LINE Messaging API        | 設備狀態查詢、防呆與規則異常的主動推播。           |
| 開發工具  | Windows Batch Script      | 提供 `start.bat` 一鍵啟動後端與模擬器。            |

---

# 7. 功能規格 (Functional Requirements)

## 7.1 多設備與啟停控制 (Equipment Control)
- 支援 10 台設備同步模擬，具備 `enabled` 開關。
- Dashboard 支援遠端控制單一設備模擬器的啟動與靜默(暫停)。

## 7.2 設備狀態機與非同步交握 (State & Command Handshake)
- 模擬器定期輪詢 PENDING 命令，處理 START/STOP/CHANGE_RECIPE 後回覆 ACK/NACK。
- FastAPI 接收 ACK 後，同步更新設備主檔 (Equipment) 的狀態與配方，並透過 WebSocket 推播更新至 Dashboard。

## 7.3 動態告警與防呆阻擋 (Alarms & Prevention)
- **Alarm Rule Engine**：將硬編碼告警改為動態規則庫，當數值越界時由 API 自動產生告警事件。
- **Recipe Mismatch 阻擋**：模擬器有 10% 機率帶入錯誤配方，API 檢核失敗時拋出 400 錯誤，阻擋機台運作。
- 發生上述事件時，即時透過 Line Bot 發送 `[規則告警]` 或 `[防呆告警]`。

## 7.4 現代化儀表板 (Modern Dashboard)
- **React App**：取代傳統 Streamlit 的重繪閃爍問題。
- 玻璃擬物化 (Glassmorphism) 深色模式設計，提升科技感。
- 透過 WebSocket 即時顯示機台狀態、Recipe 變更、與 Remote Command 的非同步狀態變更。

---

# 8. 專案目錄結構

```text
CIM_Equipment_Integration_Simulator/
├── app/
│   ├── main.py                 # FastAPI 進入點 & WS Manager
│   ├── routers/                # Equipment, Rules, LineBot APIs
│   ├── models/                 # SQLAlchemy 資料表定義
│   └── database.py             # SQLite/PostgreSQL 連線配置
├── simulator/
│   └── equipment_simulator.py  # 多執行緒設備模擬器核心
├── dashboard-react/            # 現代化 React 前端專案
│   ├── src/App.jsx             # React WebSocket 介面
│   └── src/App.css             # Glassmorphism 美學設計
├── dashboard/                  # (Legacy) Streamlit 介面
├── CIM_Equipment_Integration_Simulator_完整規格書.md
├── start.bat                   # Windows 一鍵啟動腳本
└── GEMINI.md                   # Agent 開發筆記與追蹤
```

---

# 9. 履歷與面試亮點

## 履歷專案描述 (Resume Description)
> **Side Project：CIM Equipment Integration Simulator 2.0 (半導體設備整合模擬平台)**
> - 結合封測廠實務與軟體開發經驗，設計並實作具備 10 台設備併發連線的 CIM 模擬平台。
> - 使用 **Python (FastAPI)** 開發 CIM Host，實作設備動態規則告警引擎、Recipe Mismatch 防呆攔截與 Remote Command 遠端控制交握。
> - 導入 **WebSockets** 與 **React (Vite)** 打造高質感現代化前端儀表板，解決傳統輪詢畫面閃爍問題，達成毫秒級狀態同步。
> - 整合 **LINE Bot** 主動推播機制，當機台發生防呆錯誤或數值異常時，第一時間傳遞警報至工程師手機。

## 面試 Demo 亮點
1. **展示完整資料流**：從 Python 模擬器 -> FastAPI -> DB -> WebSocket -> React UI，證明全端架構掌握度。
2. **防呆與交握機制**：實際下發 CHANGE_RECIPE 觀察 PENDING -> ACK 交握，以及展示 10% Mismatch 機率被 Host 阻擋並發送 Line 的防呆情境。
3. **解決問題的能力**：分享為何從 Streamlit 轉換到 React + WebSockets (為了解決輪詢閃爍與提升 UI 即時性體驗)。
