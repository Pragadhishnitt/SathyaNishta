#!/bin/bash

echo "Checking service health..."

# Services to check
services=("sathya_traefik" "sathya_api" "sathya_frontend" "sathya_neo4j")

for service in "${services[@]}"; do
  # Check if container is running
  if [ "$(docker ps -q -f name=$service)" ]; then
    # Get health status if available, or just running state
    status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $service 2>/dev/null)
    echo "$service: $status"
  else
    echo "$service: not running"
  fi
done
