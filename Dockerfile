FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose the port for FastAPI
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the FastAPI application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
