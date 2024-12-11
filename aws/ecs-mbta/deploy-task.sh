#!/bin/bash

# create task
aws ecs register-task-definition --cli-input-json file://task.json

# run task
aws ecs run-task --cluster iot2 --task-definition mbta_vehicles
