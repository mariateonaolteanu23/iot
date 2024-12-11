import requests
import logging
from datetime import datetime
from influxdb import InfluxDBClient
import schedule
import os
import time
import pytz
import traceback

client_v = None
client_c = None

vid = os.getenv("VID")
rid = os.getenv("RID")

API_KEY = os.getenv("API_KEY")
INFLUX_DB = os.getenv("INFLUX_DB")

MBTA_URL = "https://api-v3.mbta.com/"
VEHICLE_URL = lambda vid: f"{MBTA_URL}vehicles/{vid}"
SCHEDULE_URL = lambda trip, stop: f"{MBTA_URL}schedules?filter[trip]={trip}&filter[stop]={stop}"
PREDICTION_URL = lambda trip, stop: f"{MBTA_URL}predictions?filter[trip]={trip}&filter[stop]={stop}"
CHANGE_URL =  lambda route: f"{MBTA_URL}vehicles?filter[route_type]=3&filter[route]={route}"
LOG_DATE_FORMAT='%Y-%m-%d %H:%M:%S'

HEADERS = { 
    "Accept": "application/json",
    "X-API-Key": f"{API_KEY}"
}

LIMIT = "x-ratelimit-remaining"
WAIT = "x-ratelimit-reset"

FEATURES = ["bearing", "latitude", "longitude"]
TAGS = ["revenue", "occupancy_status", "current_status", "current_stop_sequence"]

def get_time_diff(t1, t2):
    t1 = datetime.fromisoformat(t1)
    t2 = datetime.fromisoformat(t2)    
    diff = t1 - t2
    return diff.total_seconds()

def get_time():
    curr = datetime.now(pytz.utc)
    tz = pytz.timezone("America/New_York")
    t = curr.astimezone(tz)
    return t.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

def get_tags(data):
    tags = {}
    
    for tag in TAGS:
        try:
            tags[tag] = data["attributes"][tag]   
        except:
            logging.error(f"Couldn't find field {tag} in API response!")
    
    for rel in ['route', 'stop', 'trip']:
        tags[rel] = data["relationships"][rel]["data"]["id"]
    
    tags["id"] = data["id"]
    
    return tags

def _call(url):
    global vid
    global rid

    response = requests.get(url)

    if response.status_code == 429:
        limit = int(response.headers[LIMIT])
        if limit == 0:
            time_to_wait = int(response.headers[WAIT]) - int(time.time())
            logging.warning(f"Reached limit of calls - Waiting {time_to_wait}s ...")
            time.sleep(time_to_wait)
            
            response = requests.get(url)
            if response.status_code == 200:
                return response
    
    # bus is not running => use another bus on the same route        
    if response.status_code == 404:
        response = _call(CHANGE_URL(rid))
        logging.warning(f"Bus {vid} is no longer running")

        if response.status_code == 200:
            new_vid = response.json()["data"][0]["id"]
            body = [{
                "measurement": f'change',
                "time": str(get_time()),
                "tags": {"new_id": new_vid, "old_id": "vid"},
                "fields": {
                    "data": 1
                }
            }]
            try:
                client_c.write_points(body)
                logging.info(f"Change is logged in the DB.")
            except Exception as e:
                logging.error("Couldn't write to CHANGES database")
                logging.error(traceback.format_exc())
            
            vid = new_vid
            response = _call(VEHICLE_URL(vid))

    if response.status_code != 200:
        logging.error(f"Requesting data failed for {url}")
    return response

# gets data from bus
def mbta_vehicle():
    global vid    
    response = _call(VEHICLE_URL(vid))

    try:
        if response.status_code == 200:
            timestamp = get_time()
            logging.info(f"Received data for vehicle {vid}")    
            data = response.json()["data"]

            body = []
            trip_id = data["relationships"]["trip"]["data"]["id"]
            stop_id = data["relationships"]["stop"]["data"]["id"]
            
            sch = _call(SCHEDULE_URL(trip_id, stop_id))
            pred = _call(PREDICTION_URL(trip_id, stop_id))
            
            delay = None
            target = "arrival_time"

            if sch.status_code == 200 and pred.status_code == 200:
                try:
                    sch = sch.json()
                    pred = pred.json()

                    if len(sch["data"]) != 0 and len(pred["data"]) != 0:
                        sch = sch["data"][0]["attributes"]
                        pred = pred["data"][0]["attributes"]
                    
                        if sch[target] == None:
                            target = "departure_time"

                        delay = get_time_diff(pred[target], sch[target]) 
                        
                        logging.info(f"{pred[target]} {sch[target]}")           
                        if delay < 0:
                            delay = 0

                        logging.info(f"Vehicle {vid} is late by {delay} seconds")  
                except:
                    logging.info("Couldn't compute delay")

            tags = get_tags(data)

            data = data["attributes"]
            
            for feature in FEATURES:
                try:
                    value = data[feature]
                    entry = {
                        "measurement": f'{feature}',
                        "time": str(timestamp),
                        "tags": tags,
                        "fields": {
                            "data": float(value)
                        }
                    }
                    body.append(entry)
                except:
                    logging.error(f"Couldn't find field {feature} in API response!")
            if delay != None:
                body.append({
                        "measurement": "delay",
                        "time": str(timestamp),
                        "tags": tags,
                        "fields": {
                            "data": float(delay)
                        }
                    })
            try:
                client_v.write_points(body)
                logging.info(f"Vehicle {vid} data is written in the DB.")
            except Exception as e:
                logging.error("Couldn't write to VEHICLES database")
                logging.error(traceback.format_exc())
    except:
        logging.error("Something unexpected happened")

def init_scheduler():
    schedule.every(5).seconds.do(mbta_vehicle)

if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s:%(asctime)s %(message)s', 
                    level=logging.INFO, datefmt=LOG_DATE_FORMAT)

    client_v = InfluxDBClient(INFLUX_DB, port=8086, username=os.getenv("USERNAME"), 
                                                password=os.getenv("PASSWORD"), 
                                                database='VEHICLES')
    logging.info("Connected to VEHICLES DB.")

    client_c = InfluxDBClient(INFLUX_DB, port=8086, username=os.getenv("USERNAME"), 
                                                password=os.getenv("PASSWORD"), 
                                                database='CHANGES')
    logging.info("Connected to CHANGES DB.")

    mbta_vehicle() # sanity check
    init_scheduler()

    while True:
        schedule.run_pending()
        time.sleep(1)
