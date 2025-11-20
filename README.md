# 中央氣象署即時溫度站資料爬蟲

這是一個用於爬取中央氣象署 OpenData 平台即時氣象站資料的 Python 專案，可自動抓取氣溫和氣壓資料並儲存至 MySQL 資料庫。

## 功能特色

- 🌡️ **即時氣象資料**：自動抓取溫度和氣壓資料
- 🗄️ **資料庫整合**：支援 MySQL 資料庫儲存
- 🔄 **智慧更新**：自動檢查測站是否存在並進行資料更新
- 📝 **完整日誌**：詳細的執行記錄和錯誤追蹤
- 🏗️ **模組化設計**：清晰的架構便於維護和擴展

## 專案結構

```
├── config/
│   └── settings.py          # 配置設定
├── core/
│   ├── __init__.py
│   ├── Crawler.py          # 主要爬蟲類別
│   └── database.py         # 資料庫操作
├── data/
│   └── stations.json       # 測站資訊檔案
├── logs/                   # 日誌檔案目錄
├── utils/
│   ├── __init__.py
│   └── load_stations.py    # 載入測站工具
├── .env                    # 環境變數配置
├── .env.example           # 環境變數範例
├── main.py                # 主程式入口
└── README.md              # 專案說明文件
```

## 安裝與設定

### 1. 安裝相依套件

```bash
pip install requests pymysql python-dotenv
```

### 2. 環境設定

複製 `.env.example` 為 `.env` 並填入相關資訊：

```bash
# CWA API 設定
CWA_API_KEY=你的API金鑰

# MySQL 資料庫設定
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的資料庫密碼
DB_NAME=資料庫名稱
```

### 3. 取得 CWA API 金鑰

1. 前往 [中央氣象署 OpenData 平台](https://opendata.cwa.gov.tw/)
2. 註冊帳號並申請 API 金鑰
3. 將金鑰填入 `.env` 檔案中的 `CWA_API_KEY`

### 4. 資料庫設定

建立所需的 MySQL 資料表：

```sql
-- 測站資料表
CREATE TABLE weather_station (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 氣象資料表
CREATE TABLE weather_temperature (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_id VARCHAR(20) NOT NULL,
    temp DECIMAL(5,1),
    pressure DECIMAL(7,2),
    obs_time DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES weather_station(id) ON DELETE CASCADE,
    UNIQUE KEY unique_station_time (station_id, obs_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 使用方法

### 基本執行

```bash
python main.py
```

### 程式流程

1. **載入配置**：讀取環境變數和測站列表
2. **API 請求**：向中央氣象署 API 請求即時資料
3. **資料處理**：解析 JSON 資料並進行格式轉換
4. **測站管理**：檢查測站是否存在，不存在則新增
5. **資料儲存**：將氣象資料儲存至資料庫
6. **日誌記錄**：完整記錄執行過程和結果

## API 資料格式

本專案使用中央氣象署的即時氣象站觀測資料 API：
- **資料集代碼**：O-A0001-001
- **主要欄位**：
  - `StationId`: 測站編號
  - `StationName`: 測站名稱
  - `ObsTime.DateTime`: 觀測時間
  - `WeatherElement.AirTemperature`: 氣溫
  - `WeatherElement.AirPressure`: 氣壓

## 測站資料

測站清單儲存在 `data/stations.json`，格式如下：

```json
[
    {
        "StationId": "C0M750",
        "StationName": "布袋"
    },
    {
        "StationId": "C0V620",
        "StationName": "永安"
    }
]
```

## 日誌系統

### 日誌等級
- **INFO**：一般執行資訊
- **DEBUG**：詳細除錯資訊
- **WARNING**：警告訊息
- **ERROR**：錯誤訊息

### 日誌檔案
- 檔案位置：`logs/weather_crawler_YYYYMMDD.log`
- 自動按日期分檔
- 同時輸出至控制台和檔案

### 範例日誌
```
2025-11-21 09:15:30 - weather_crawler - INFO - 開始執行天氣資料爬蟲程式
2025-11-21 09:15:31 - weather_crawler.crawler - INFO - 準備抓取 5 個測站的資料
2025-11-21 09:15:32 - weather_crawler.database - INFO - 資料庫連線建立成功
2025-11-21 09:15:33 - weather_crawler - INFO - 程式執行完成 - 成功儲存: 5 筆, 錯誤: 0 筆
```

## 錯誤處理

### 常見問題與解決方法

1. **API 金鑰錯誤**
   ```
   錯誤：HTTP 401 Unauthorized
   解決：檢查 .env 中的 CWA_API_KEY 是否正確
   ```

2. **資料庫連線失敗**
   ```
   錯誤：資料庫連線錯誤
   解決：檢查資料庫服務是否啟動，帳號密碼是否正確
   ```

3. **測站資料載入失敗**
   ```
   錯誤：無法載入測站列表
   解決：確認 data/stations.json 檔案存在且格式正確
   ```


### 使用 Windows 工作排程器

1. 開啟「工作排程器」
2. 建立基本工作
3. 設定觸發程序（時間間隔）
4. 動作設定為執行 `python main.py`

## 效能最佳化

- **資料庫連線池**：使用 context manager 管理連線
- **重複資料處理**：使用 `ON DUPLICATE KEY UPDATE` 避免重複插入
- **錯誤重試**：API 請求失敗時的處理機制
- **記憶體管理**：及時關閉資料庫連線
