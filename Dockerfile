FROM python:3.11-slim-bookworm

WORKDIR /app

# Install curl and gnupg to setup repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Add Raspberry Pi repository key and source
# This provides the correct libcamera versions with IPA support for Raspberry Pi 5
RUN curl -fsSL https://archive.raspberrypi.org/debian/raspberrypi.gpg.key | gpg --dearmor -o /usr/share/keyrings/raspberrypi-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/raspberrypi-archive-keyring.gpg] http://archive.raspberrypi.org/debian bookworm main" > /etc/apt/sources.list.d/raspi.list

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcamera0 \
    libcamera-tools \
    gstreamer1.0-libcamera \
    python3-opencv \
    python3-numpy \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-tools \
    gstreamer1.0-libav \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# Add system packages to PYTHONPATH
ENV PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH"

# Copy requirements
COPY requirements.txt .
# We use --break-system-packages because we are mixing apt and pip
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy source code
COPY src/ src/
COPY config/ config/

# Create data directory
RUN mkdir -p data/images

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
