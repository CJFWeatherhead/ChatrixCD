FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create virtual environment
RUN uv venv /app/.venv

# Set environment variables to use the venv
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV PYTHONUNBUFFERED=1

# Copy dependency files
COPY requirements.txt .
COPY pyproject.toml .
COPY setup.py .
COPY README.md .

# Install dependencies using uv
RUN uv pip install --no-cache -r requirements.txt

# Copy application code
COPY chatrixcd/ ./chatrixcd/

# Install the application in the venv
RUN uv pip install --no-cache -e .

# Create store directory
RUN mkdir -p /app/store

# Run the bot
CMD ["chatrixcd"]
