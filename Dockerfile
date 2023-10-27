# Use the specified Python version
FROM python:3.11.4-slim-buster

# Configure Poetry
ENV POETRY_VERSION=1.6.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install poetry separated from system interpreter
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Set the working directory
WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry install

# Copy the flask app to the working directory
COPY . /app

# Run the application
EXPOSE 8000
CMD [ "poetry", "run", "python", "./run.py" ]
