FROM python:3.13-slim-bookworm

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Upgrade pip
RUN python -m pip install --upgrade pip

# Install the application dependencies
WORKDIR /requirements
COPY src/requirements.txt .
RUN python -m pip install -r requirements.txt

# Copy the application code
WORKDIR /app
COPY . /app

# Creates a non-root user to run the application and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Run the application
CMD ["python", "./src/teslamate_telegram_bot.py"]
