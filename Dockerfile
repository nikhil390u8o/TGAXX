# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
# We add gcc and python3-dev to compile C extensions like tgcrypto
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Ensure sessions directory exists
RUN mkdir -p sessions

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot (Ensure your filename is correct, e.g., main.py)
CMD ["python", "main.py"]
