FROM python:3.11-slim

WORKDIR /app

# Copy the entire project (build context is parent directory)
COPY . /app/

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "example.__main__:app", "--host", "0.0.0.0", "--port", "8000"]

