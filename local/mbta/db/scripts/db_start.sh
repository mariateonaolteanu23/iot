#!/bin/bash

if !(influx -execute 'SHOW DATABASES' | grep -q 'CHANGES'); then 
    influx -execute 'CREATE DATABASE "CHANGES" WITH DURATION INF'
fi;

if !(influx -execute 'SHOW DATABASES' | grep -q 'VEHICLES'); then 
    influx -execute 'CREATE DATABASE "VEHICLES" WITH DURATION INF'
fi;