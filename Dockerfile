# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create asset directory if it doesn't exist
RUN mkdir -p asset

# Create a default logo if it doesn't exist
RUN if [ ! -f asset/logo.png ]; then \
    echo "Creating placeholder logo"; \
    python -c "from PIL import Image; img = Image.new('RGB', (150, 150), color='white'); img.save('asset/logo.png')"; \
    fi

# Expose port 8501 (Streamlit default)
EXPOSE 8501

# Set the default command to run the Streamlit app
CMD ["streamlit", "run", "invoice.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"] 