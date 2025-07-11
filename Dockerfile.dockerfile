FROM python:3.9-slim

WORKDIR /usr/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install dbt
RUN pip install dbt-postgres

# Copy project files
COPY . .

# Set environment variables
ENV PYTHONPATH=/usr/app
ENV DBT_PROFILES_DIR=/usr/app/dbt

CMD ["bash"]