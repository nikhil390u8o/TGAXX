# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
# sqlite3 is needed for database management
# rm and other utils are usually present in slim, but we ensure basic tools
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the sessions directory to ensure it exists
RUN mkdir -p sessions

# Set environment variables (optional, but good practice)
ENV PYTHONUNBUFFERED=1

# Command to run your bot
# Replace 'main.py' with the actual name of your python file
CMD ["python", "main.py"]
