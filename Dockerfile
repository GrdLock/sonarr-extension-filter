FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create directory for config and logs
RUN mkdir -p /config /app/logs

# Expose ports
EXPOSE 5000 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=5)"

# Run startup script to launch both services
CMD ["/app/start.sh"]
