FROM python:3.11-slim

WORKDIR /app

# Copy everything first (simpler for editable install)
COPY . /app/

# Install the package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Expose the port
EXPOSE 8000

# Run the application
# Set PYTHONPATH to ensure the package can be imported
ENV PYTHONPATH=/app
CMD ["uvicorn", "{PACKAGE_NAME}.main:app", "--host", "0.0.0.0", "--port", "8000"]

