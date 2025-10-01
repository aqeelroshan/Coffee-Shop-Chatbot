FROM python:3.10-slim

# Create app directory
RUN mkdir /app
WORKDIR /app

# Copy requirements and install dependencies with pinned versions
COPY requirements.txt requirements.txt

# Upgrade pip first
RUN pip install --upgrade pip

# Install pinned versions to avoid binary incompatibility
RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.3.2 \
    pyarrow==16.1.0 \
    numba==0.60.0 \
    bottleneck==1.3.7 \
    -r requirements.txt

# Copy your app code
COPY recommendation_objects/ recommendation_objects/
COPY agents/ agents/
COPY agent_controller.py agent_controller.py
COPY main.py main.py

# Optional test file
# COPY test_input.json test_input.json

ENTRYPOINT ["python", "main.py"]
