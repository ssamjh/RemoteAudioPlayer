# Use an official Python 3 image as the base image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install the required modules
RUN python3 -m pip install -U flask flask-socketio

# Specify the command to run when the container starts
CMD ["python", "./server.py"]
