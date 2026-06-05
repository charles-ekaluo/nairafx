# Start with an official lightweight Python image
# The slim variant gives us Python + minimal Linux without the extras we don't need
FROM python:3.11-slim

# Set the working directory inside the container
# All subsequent commands run from /app
WORKDIR /app

# Copy requirements first (before app code) so Docker can cache this layer
# If only the app code changes, Docker reuses this cached install step
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir keeps the image smaller by not storing pip's download cache
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code
# Doing this after pip install means code changes don't bust the dependency cache
COPY app.py .

# Document that the container listens on port 5000
# This is informational — it doesn't actually open the port
EXPOSE 5000

# The command that runs when the container starts
CMD ["python", "app.py"]
