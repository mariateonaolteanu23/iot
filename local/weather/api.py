import requests
import logging
from datetime import datetime
from influxdb import InfluxDBClient
import schedule
import pytz
import os
import time
from datetime import datetime

API_KEY = os.getenv("API_KEY")
CITY = os.getenv("CITY")
INFLUX_DB = os.getenv("INFLUX_DB")

WEATHER_URL = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}&aqi=yes"
LOG_DATE_FORMAT='%Y-%m-%d %H:%M:%S'

FEATURES = ["temp_c", "precip_mm", "humidity", "wind_kph", ]

def get_time(t):
    dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

def weather():
    global client
    
    response = requests.get(WEATHER_URL)

    if response.status_code == 200:
        data = response.json()["current"]

        logging.info(f"{CITY} time - {data['last_updated']}: {data['temp_c']}C")
        timestamp = get_time(data["last_updated"])
        
        body = []
        for feature in FEATURES:
            try:
                value = data[feature]
                entry = {
                    "measurement": f'{feature}',
                    "time": str(timestamp),
                    "tags": {"location": {CITY}},
                    "fields": {
                        "data": float(value)
                    }
                }
                body.append(entry)
            except:
                logging.error(f"Couldn't find feature {feature} in API response")
        try:
            client.write_points(body, database='WEATHER')
        except:
            logging.error("Couldn't write to WEATHER database")
    
def init_scheduler():
    schedule.every(3).hours.do(weather)

if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s', 
                    level=logging.INFO, datefmt=LOG_DATE_FORMAT)
    global client
    client = InfluxDBClient(INFLUX_DB, port=8086)
    logging.info("Connected to InfluxDB")
    
    init_scheduler()
    while True:
        schedule.run_pending()
        time.sleep(1)
    
    
    

