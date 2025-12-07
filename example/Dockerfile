FROM python:3.11-slim

WORKDIR /app

# Copy the entire project (build context is parent directory)
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    redis \
    psycopg2-binary \
    httpx \
    jinja2 \
    python-multipart \
    fastapi-swagger-dark

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "example.__main__:app", "--host", "0.0.0.0", "--port", "8000"]

