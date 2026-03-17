# 1. Use an official Python runtime as a parent image
FROM python:3.10-slim

# 2. Set the working directory in the container
WORKDIR /app

# 3. Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libglx-mesa0 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy model weights and code into the container
# Create the internal folder structure
COPY src/ ./src/
COPY weights/ ./weights/

# 6. Create the 'serve' executable shim directly in the Dockerfile
# This tells uvicorn to listen on port 8080, which is SageMaker's default.
RUN echo '#!/bin/bash\ncd /app/src && uvicorn main:app --host 0.0.0.0 --port 8080' > /usr/bin/serve \
    && chmod +x /usr/bin/serve

# 7. Expose port 8080 (SageMaker's expected port) instead of 8000
EXPOSE 8080

# 8. Set the Entrypoint to the 'serve' command we just created
# This allows SageMaker to start the container successfully.
ENTRYPOINT ["serve"]

# Force rebuild for QA.