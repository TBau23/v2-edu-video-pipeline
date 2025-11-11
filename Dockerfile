FROM python:3.11-slim

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    ffmpeg \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Gradio port
EXPOSE 7860

# Run the web app
CMD ["python", "examples/web_app.py"]
