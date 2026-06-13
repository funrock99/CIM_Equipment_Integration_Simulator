# 執行步驟 (Execution Steps)

本專案支援「Windows 一鍵啟動」、「Docker 容器化部署」與「本地直接執行 (SQLite)」三種啟動方式。

---

## 方式一：Windows 一鍵啟動 (最快)

如果您是在 Windows 環境，我們提供了整合好的批次檔，可以直接啟動所有必要服務。

```powershell
# 直接執行根目錄下的 start.bat
.\start.bat
```
這會自動幫您檢查 `.env` 並開啟三個視窗分別啟動 API、模擬器與監控面板。

---

## 方式二：使用 Docker 啟動 (建議，針對有安裝 Docker 的環境)

### 步驟 1：啟動資料庫與 CIM Host API
使用 Docker Compose 啟動 PostgreSQL 與 FastAPI 後端服務。
```powershell
# 請在專案根目錄 (E:\CIM_Equipment_Integration_Simulator) 下執行
docker-compose up -d --build
```
> **提示**：啟動完成後，您可以打開瀏覽器訪問 `http://localhost:8000/docs` 來確認 API 是否正常運行，並可檢視 Swagger API 文件。

*(完成後請接續執行下方的步驟 2 與 步驟 3)*

---

## 方式三：本地直接執行 (無 Docker 環境，使用 SQLite)

如果您的環境未安裝 Docker，系統設計已支援自動 fallback 使用 SQLite 檔案資料庫 (`cim.db`)。

### 步驟 1：啟動 CIM Host API
```powershell
# 請在專案根目錄 (E:\CIM_Equipment_Integration_Simulator) 下執行
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
> **提示**：啟動後，專案目錄下會自動生成 `cim.db` 檔案，API 文件同樣可透過 `http://localhost:8000/docs` 查看。

---

## 步驟 2：啟動 Equipment Simulator (設備模擬)
開啟 **第二個終端機** 視窗，啟動設備模擬器腳本。這會在背景中持續產生設備的狀態、感測器數據及警報，並上傳到 API。

```powershell
# 請在專案根目錄下執行
pip install requests
python simulator/equipment_simulator.py
```
> **提示**：如果一切正常，您會在終端機看到設備註冊成功及隨機產生的模擬事件輸出。請保持這個視窗開啟以維持模擬器運行。

## 步驟 3：啟動 Dashboard (監控面板)
開啟 **第三個終端機** 視窗，啟動基於 Streamlit 的網頁監控介面。

```powershell
# 請在專案根目錄下執行
pip install streamlit pandas
streamlit run dashboard/streamlit_app.py
```
> **提示**：執行後會自動開啟瀏覽器頁面 (通常為 `http://localhost:8501`)，您可以在網頁上查看即時的設備總覽、報警清單以及感測器的歷史趨勢圖。
