FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Create virtual environment using Python's built-in venv
# This isolates dependencies from the system Python
RUN python -m venv /app/.venv

# Set environment variables to use the venv
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV PYTHONUNBUFFERED=1

# Copy dependency files
COPY requirements.txt .
COPY pyproject.toml .
COPY setup.py .
COPY README.md .

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY chatrixcd/ ./chatrixcd/

# Install the application in the venv
RUN pip install --no-cache-dir -e .

# Create store directory
RUN mkdir -p /app/store

# Note: Configuration should be provided via mounted config.json file
# Example: -v ./config.json:/app/config.json:ro

# Run the bot
CMD ["chatrixcd"]
