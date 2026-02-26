#!/bin/bash
# Rebuild and restart the container
echo "Rebuilding and restarting Speed Cam Pi..."
docker compose up --build -d
echo "Done! Check logs with: docker compose logs -f"
