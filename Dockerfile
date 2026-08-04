# Stage 1: Build stage
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

# Set environment variables
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
# Compiling Python source files to bytecode
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache mount instead of linking into it
ENV UV_LINK_MODE=copy

# Set the working directory
WORKDIR /app

# Install the dependencies in their own layer, without the project itself.
# They change far less often than the source, so this layer stays cached
# across source edits. pyproject.toml and uv.lock are mounted rather than
# copied, so neither ends up in an image layer. Dependency groups are
# development only and are not installed.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --locked --no-install-project --no-default-groups

# Copy the source last: everything above stays cached when only this changes
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install the project itself into the same environment. --no-editable puts the
# code into the virtual environment, so the runtime stage does not need /app.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-default-groups

# Stage 2: Runtime stage
FROM python:3.14-slim-trixie AS app

# Set environment variables
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
# Run everything from the virtual environment copied in below
ENV PATH="/app/.venv/bin:$PATH"

# Create a non-root user and group
RUN adduser --disabled-password --gecos "" nonroot

# Copy only the resulting virtual environment from the builder stage.
# This avoids copying build tools like uv, pip and setuptools into the final
# image. Using --chown avoids a separate RUN chown command, making the image
# smaller.
COPY --chown=nonroot:nonroot --from=builder /app/.venv /app/.venv

# Switch to the non-root user
USER nonroot

# Set the working directory
WORKDIR /app

# Run the application using the installed entry point
CMD ["teslamate-telegram-bot"]
