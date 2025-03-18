FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories if not exists
RUN mkdir -p .streamlit

# Create config.toml file directly
RUN echo '[theme]\nprimaryColor="#ff00c1"\nbackgroundColor="#120458"\nsecondaryBackgroundColor="#000000"\ntextColor="#ffffff"\nfont="monospace"\n\n[server]\nenableCORS=false\nenableXsrfProtection=false\n\n[browser]\ngatherUsageStats = false' > .streamlit/config.toml

# Expose the port Streamlit runs on
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false

# Command to run the application
# REDIS_URL should be provided when running the container
CMD ["streamlit", "run", "app.py", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]