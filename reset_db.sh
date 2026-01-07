#!/bin/bash
echo "Stopping all containers..."
docker-compose down -v

echo "Removing local data directories..."
rm -rf data/mysql
mkdir -p data/mysql

echo "Pruning docker volumes..."
docker volume prune -f

echo "Starting services..."
docker-compose up -d --build