#!/bin/bash

MEASUREMENTS=("latitude" "longitude" "bearing" "delay")
RIDS=("66" "111" "23" "57" "1")

# get EC2 IP
if [ -z "$1" ]; then
  echo "Usage: $0 <EC2_IP>"
  exit 1
fi
IP=$1

# set output path
mkdir -p ../vehicle-exports

# get vehicle data
for MEASUREMENT in "${MEASUREMENTS[@]}"; do
  for ID in "${RIDS[@]}"; do
    q="SELECT * FROM \"$MEASUREMENT\" WHERE route='$ID'"
    curl -G "http://$IP:8086/query" \
        --data-urlencode "db=VEHICLES" \
        --data-urlencode "q=$q" \
        -H "Accept: application/csv" \
        -o ../vehicle-exports/${MEASUREMENT}_route_${ID}.csv
  done
done

# get change log
curl -G "http://$IP:8086/query" \
    --data-urlencode "db=CHANGES" \
    --data-urlencode "q=SELECT * FROM change" \
    -H "Accept: application/csv" \
    -o ../vehicle-exports/changes.csv

python concat_v.py "${MEASUREMENTS[@]}"