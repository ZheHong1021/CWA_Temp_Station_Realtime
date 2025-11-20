import logging
import os
from datetime import datetime
from core.Crawler import Crawler
from core.database import WeatherDatabase

# 設定 logger
def setup_logger():
    # 建立 logs 目錄（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # 設定日誌格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 建立 logger
    logger = logging.getLogger('weather_crawler')
    logger.setLevel(logging.INFO)

    # 避免重複添加 handler
    if not logger.handlers:
        # 檔案 handler
        file_handler = logging.FileHandler(
            f'logs/weather_crawler_{datetime.now().strftime("%Y%m%d")}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # 控制台 handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

if __name__ == "__main__":
    logger = setup_logger()

    logger.info("開始執行天氣資料爬蟲程式")

    try:
        crawler = Crawler()
        data = crawler.fetch()

        if not data:
            logger.error("無法取得API資料")
            exit(1)

        # 主要資料都在 'records' 欄位下的Station陣列中
        stations = data.get('records', {}).get('Station', [])
        logger.info(f"取得 {len(stations)} 個測站資料")

        with WeatherDatabase() as db:
            saved_count = 0
            error_count = 0

            for station in stations:
                station_id = station.get('StationId', None)
                station_name = station.get('StationName', None)
                obsTime = station['ObsTime']['DateTime']
                temp = station["WeatherElement"]["AirTemperature"]
                pressure = station["WeatherElement"]["AirPressure"]

                if not station_id:
                    logger.warning("測站ID為空，跳過此筆資料")
                    continue

                # 檢查並新增測站
                if not db.station_exists(station_id):
                    if db.insert_station(station_id, station_name):
                        logger.info(f"新增測站: {station_id} - {station_name}")
                    else:
                        logger.error(f"新增測站失敗: {station_id} - {station_name}")

                # 處理氣象資料
                if temp and temp != '-999' and pressure and pressure != '-999' and obsTime:
                    try:
                        # 轉換時間格式 (處理 ISO 8601 格式)
                        # 移除時區資訊，只保留日期時間部分
                        clean_time = obsTime.split('+')[0].replace('T', ' ')
                        obs_datetime = datetime.strptime(clean_time, '%Y-%m-%d %H:%M:%S')

                        # 儲存氣象資料
                        if db.insert_or_update_temperature(station_id, float(temp), float(pressure), obs_datetime):
                            saved_count += 1
                            logger.debug(f"成功儲存測站 {station_id} 資料: 溫度={temp}°C, 氣壓={pressure}hPa")

                    except (ValueError, TypeError) as e:
                        error_count += 1
                        logger.error(f"處理測站 {station_id} 資料時發生錯誤: {e}")
                        logger.debug(f"錯誤詳細資訊 - 原始時間: {obsTime}, 氣溫: {temp}, 氣壓: {pressure}")
                else:
                    logger.warning(f"測站 {station_id} 資料不完整或無效，跳過處理")

            logger.info(f"程式執行完成 - 成功儲存: {saved_count} 筆, 錯誤: {error_count} 筆")

    except Exception as e:
        logger.error(f"程式執行過程中發生嚴重錯誤: {e}", exc_info=True)
        exit(1)

