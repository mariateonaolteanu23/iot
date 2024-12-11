#!/bin/bash

# create task
aws ecs register-task-definition --cli-input-json file://task.json

# create service
aws ecs create-service --cli-input-json file://service.json

# run task on service
aws ecs update-service \
    --cluster iot \
    --service vehicle-111 \
    --desired-count 1