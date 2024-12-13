#!/bin/bash

MEASUREMENTS=("temp_c" "precip_mm" "humidity" "wind_kph")

# get EC2 IP
if [ -z "$1" ]; then
  echo "Usage: $0 <EC2_IP>"
  exit 1
fi
IP=$1

# set output path
mkdir -p ../weather-exports

# get weather data
for MEASUREMENT in "${MEASUREMENTS[@]}"; do
  curl -G "http://$IP:8086/query" \
      --data-urlencode "db=WEATHER" \
      --data-urlencode "q=SELECT * FROM \"$MEASUREMENT\"" \
      -H "Accept: application/csv" \
      -o ../weather-exports/${MEASUREMENT}.csv
done

python concat_w.py "${MEASUREMENTS[@]}"