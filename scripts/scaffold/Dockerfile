FROM python:3.11-slim

WORKDIR /app

# Copy pyproject.toml first for better caching
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy the rest of the application
COPY . /app/

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "{PACKAGE_NAME}.main:app", "--host", "0.0.0.0", "--port", "8000"]

