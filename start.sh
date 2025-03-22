#!/bin/bash

# Start the Flask application using gunicorn
gunicorn -b 0.0.0.0:5000 main:app