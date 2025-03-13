# Docker FROM command specifies the base container image
# Our base image is Linux with python pre-installed
FROM python:3.13-slim

# Set the environment variable
ENV APP_HOME /app

# Set up a working directory inside the container
WORKDIR $APP_HOME

# Install dependencies inside the container
COPY pyproject.toml $APP_HOME/pyproject.toml

RUN pip install poetry

# Copy other files to the container's working directory
COPY . .

# Indicate the port where the application runs inside the container
EXPOSE 3000

# Run our application inside the container
CMD ["python", "main.py"]