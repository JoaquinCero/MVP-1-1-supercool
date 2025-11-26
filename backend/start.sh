#!/usr/bin/env bash
# Render usa la variable de entorno $PORT para el puerto, y necesita 0.0.0.0
uvicorn main:app --host 0.0.0.0 --port $PORT