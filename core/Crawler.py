import logging
import requests
from datetime import datetime
from config.settings import CWA_API_KEY
from utils import load_stations
from .database import WeatherDatabase

class Crawler:
    def __init__(self):
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/"
        self.dataset_id = "O-A0001-001"
        self.api_key = CWA_API_KEY
        self.logger = logging.getLogger('weather_crawler.crawler')

    def fetch(self):
        url = f"{self.base_url}{self.dataset_id}"

        # 載入測站ID列表
        stations = load_stations()
        if not stations:
            self.logger.error("無法載入測站列表")
            return None

        station_ids = list(map(lambda s: s['StationId'], stations))
        self.logger.info(f"準備抓取 {len(station_ids)} 個測站的資料")

        params = {
            'Authorization': self.api_key, # API金鑰
            'StationId': ','.join(station_ids), # 多個測站ID以逗號分隔
            'WeatherElement': 'AirTemperature,AirPressure' # 只抓取氣溫和氣壓
        }

        try:
            self.logger.debug(f"發送API請求: {url}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            self.logger.info("API資料取得成功")
            return data
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API請求錯誤: {e}")
            return None

    def save_to_database(self, weather_data):
        if not weather_data:
            print("No data to save")
            return False

        # 載入測站資料作為參考
        stations = load_stations()
        station_dict = {s['StationId']: s['StationName'] for s in stations}

        with WeatherDatabase() as db:
            # 處理API回傳的資料
            locations = weather_data.get('records', {}).get('location', [])
            saved_count = 0

            for location in locations:
                station_id = location.get('StationId')
                station_name = location.get('StationName', station_dict.get(station_id, 'Unknown'))
                observation_time = location.get('ObsTime', {}).get('DateTime')

                if not station_id:
                    continue

                # 檢查並新增測站
                if not db.station_exists(station_id):
                    db.insert_station(station_id, station_name)
                    print(f"New station added: {station_id} - {station_name}")

                # 處理氣溫資料
                weather_elements = location.get('WeatherElement', [])
                for element in weather_elements:
                    if element.get('ElementName') == 'AirTemperature':
                        temperature = element.get('ElementValue')

                        if temperature and temperature != '-999' and observation_time:
                            try:
                                # 轉換時間格式
                                obs_datetime = datetime.strptime(observation_time, '%Y-%m-%d %H:%M:%S')

                                # 儲存氣溫資料
                                if db.insert_or_update_temperature(station_id, float(temperature), obs_datetime):
                                    saved_count += 1

                            except (ValueError, TypeError) as e:
                                print(f"Error processing temperature data for {station_id}: {e}")

            print(f"Successfully saved {saved_count} temperature records to database")
            return saved_count > 0

    def crawl_and_save(self):
        print("Starting weather data crawl and save to database...")
        data = self.fetch()
        if data:
            return self.save_to_database(data)
        else:
            print("Failed to fetch data")
            return False
