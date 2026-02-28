#!/bin/bash
# Start gunicorn with configuration file
exec gunicorn main:application --config gunicorn.conf.py
