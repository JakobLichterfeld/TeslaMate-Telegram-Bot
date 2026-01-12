FROM python:3.14-slim-bookworm

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Upgrade pip
RUN python -m pip install --upgrade pip

WORKDIR /app

# Copy files needed for installation and install dependencies
# This copies pyproject.toml and the src directory, then installs the package.
# This improves Docker layer caching, as dependencies are only re-installed
# when pyproject.toml or the src directory changes.
COPY pyproject.toml .
COPY src ./src
RUN python -m pip install .

# Creates a non-root user to run the application and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Run the application using the installed entry point
CMD ["teslamate-telegram-bot"]
