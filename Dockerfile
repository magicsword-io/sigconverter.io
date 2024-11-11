FROM python:3.11.4-slim-buster

# install dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    jq \
    python3-venv \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for main app dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# define work directory
WORKDIR /app/

# Copy pyproject.toml first
COPY pyproject.toml uv.lock ./

# Install main application dependencies with uv
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -e .

# Copy application files
COPY app /app/app

# Make setup script executable
RUN chmod +x /app/app/setup.py

# Setup Sigma versions using pip
RUN cd /app/app && python setup.py

# launch application
EXPOSE 8000
CMD [".venv/bin/python", "-m", "app.main"]
