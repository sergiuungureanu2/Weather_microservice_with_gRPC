#!/bin/bash
set -e

python3 server/weather_server.py &

sleep 5
python3 frontend/dashboard.py
