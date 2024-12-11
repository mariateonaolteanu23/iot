#!/bin/bash

if !(influx -execute 'SHOW DATABASES' | grep -q 'WEATHER'); then 
    influx -execute 'CREATE DATABASE "WEATHER" WITH DURATION INF'
fi;