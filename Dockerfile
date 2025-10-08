FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY chatrixcd/ ./chatrixcd/
COPY setup.py .
COPY README.md .

# Install the application
RUN pip install -e .

# Create store directory
RUN mkdir -p /app/store

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["chatrixcd"]
