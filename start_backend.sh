#!/bin/bash
# Start Open-Detective Backend on the correct port (8081)
source .venv/bin/activate
uvicorn src.backend.main:app --reload --port 8081
