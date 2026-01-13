# Stage 1: Build stage
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

# Set environment variables
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
# Compiling Python source files to bytecode
ENV UV_COMPILE_BYTECODE=1

# Set the working directory
WORKDIR /app

# Copy project definition
COPY pyproject.toml .
COPY uv.lock .
COPY src ./src

# Install the package and its dependencies into a specific prefix
# This keeps the build environment clean.
RUN uv pip install . --prefix=/opt/built

# Stage 2: Runtime stage
FROM python:3.14-slim-trixie AS app

# Set environment variables
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Create a non-root user and group
RUN adduser --disabled-password --gecos "" nonroot

# Copy only the installed application and its dependencies from the builder stage.
# This avoids copying build tools like pip, setuptools etc. into the final image.
# Using --chown avoids a separate RUN chown command, making the image smaller.
COPY --chown=nonroot:nonroot --from=builder /opt/built /usr/local

# Switch to the non-root user
USER nonroot

# Set the working directory
WORKDIR /app

# Run the application using the installed entry point
CMD ["teslamate-telegram-bot"]
