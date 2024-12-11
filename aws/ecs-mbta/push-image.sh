#!/bin/bash

aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin <aws-id>.dkr.ecr.eu-north-1.amazonaws.com
docker build -t <aws-id>.dkr.ecr.eu-north-1.amazonaws.com/mbta:latest .
docker push  <aws-id>.dkr.ecr.eu-north-1.amazonaws.com/mbta:latest
