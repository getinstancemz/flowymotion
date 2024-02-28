# Use the official Python image as the base image
FROM python:3.8-slim

# Install any additional libraries or tools you need here
RUN apt-get update && apt-get install -y git vim \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory

WORKDIR /var/flowymotion

# Copy your requirements.txt file and install the required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
