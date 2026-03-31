FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies


# Copy project
COPY . .

# Upgrade pip
RUN pip install --upgrade pip

# Install python packages
RUN pip install --no-cache-dir -r requirements.txt

# Create downloads folder
RUN mkdir -p /app/downloads

CMD ["python", "main.py"]
