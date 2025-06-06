# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and test code into the container
COPY ./client_node ./client_node
COPY ./tests ./tests

# Expose the ports the application will use
EXPOSE 6000 8000 8001 8080