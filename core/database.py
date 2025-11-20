import logging
import pymysql
import pymysql.cursors
from config.settings import DATABASE_CONFIG

class WeatherDatabase:
    def __init__(self):
        self.config = DATABASE_CONFIG
        self.connection = None
        self.logger = logging.getLogger('weather_crawler.database')

    def connect(self):
        try:
            self.connection = pymysql.connect(**self.config)
            self.logger.info("資料庫連線建立成功")
            return True
        except pymysql.Error as e:
            self.logger.error(f"資料庫連線錯誤: {e}")
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.logger.info("資料庫連線已關閉")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def station_exists(self, station_id):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT COUNT(*) FROM weather_station WHERE id = %s"
                cursor.execute(sql, (station_id,))
                result = cursor.fetchone()
                exists = result[0] > 0
                self.logger.debug(f"測站 {station_id} 存在檢查: {'是' if exists else '否'}")
                return exists
        except pymysql.Error as e:
            self.logger.error(f"檢查測站存在時發生錯誤: {e}")
            return False

    def insert_station(self, station_id, station_name):
        try:
            with self.connection.cursor() as cursor:
                sql = """
                INSERT INTO weather_station (id, name)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name)
                """
                cursor.execute(sql, (station_id, station_name))
                self.connection.commit()
                self.logger.debug(f"測站資料庫操作完成: {station_id} ({station_name})")
                return True
        except pymysql.Error as e:
            self.logger.error(f"新增測站時發生錯誤: {e}")
            return False

    def insert_or_update_temperature(self, station_id, temp, pressure, observation_time):
        try:
            with self.connection.cursor() as cursor:
                sql = """
                INSERT INTO weather_temperature (station_id, temp, pressure, obs_time)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    temp = VALUES(temp),
                    pressure = VALUES(pressure),
                    updated_at = CURRENT_TIMESTAMP
                """
                cursor.execute(sql, (station_id, temp, pressure, observation_time))
                self.connection.commit()
                self.logger.debug(f"氣象資料已儲存 - 測站: {station_id}, 溫度: {temp}°C, 氣壓: {pressure}hPa, 時間: {observation_time}")
                return True
        except pymysql.Error as e:
            self.logger.error(f"儲存氣象資料時發生錯誤: {e}")
            return False