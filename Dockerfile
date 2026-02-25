FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
# python3-opencv is needed for GStreamer support which isn't in the PyPI wheels
# libcamera-tools and gstreamer plugins are needed for Pi 5 camera stack
# gstreamer1.0-libcamera is CRITICAL for libcamerasrc
RUN apt-get update && apt-get install -y \
    python3-opencv \
    python3-numpy \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-tools \
    gstreamer1.0-libav \
    gstreamer1.0-libcamera \
    libcamera-tools \
    v4l-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Add system packages to PYTHONPATH so the container's Python can find cv2
ENV PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH"

# Copy requirements
COPY requirements.txt .
# We use --break-system-packages because we are mixing apt and pip,
# but effectively we are installing into /usr/local which is fine for this container image.
# However, newer pip might complain.
# actually python:3.11 image usually allows pip install without --break-system-packages unless it's strictly managed.
# But since we are on bookworm, it is PEP 668 enabled.
# The python:3.11-slim image is not marked as externally managed in the same way as a full Debian system
# because it uses a custom python install in /usr/local.
# BUT, I am installing python3-opencv which installs to /usr/lib/python3/dist-packages (system python).
# I am pointing PYTHONPATH to it.
# The `pip install` will go to /usr/local/lib/python3.11/site-packages.
# This should be fine.
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY config/ config/

# Create data directory
RUN mkdir -p data/images

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
