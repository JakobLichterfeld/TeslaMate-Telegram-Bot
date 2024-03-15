FROM python:3.11-slim-bookworm

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# install the OS build deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    python-dev \
    python3-dev \
    openssl \
    cargo \
    && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Update pip
RUN python -m pip install --upgrade pip

# Copy requirements.txt and install requirements
WORKDIR /requirements
COPY src/requirements.txt .
RUN python -m pip install -r requirements.txt

# Copy the rest of the code
WORKDIR /app
COPY . /app

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "./src/teslamte_telegram_bot.py"]
