FROM python:3.11-slim

WORKDIR /app

# Copy realm-sync-api source first (parent directory)
# Copy the entire project root to maintain proper structure
COPY realm_sync_api /realm_sync_api_source/realm_sync_api
COPY scripts /realm_sync_api_source/scripts
COPY pyproject.toml /realm_sync_api_source/
COPY README.md /realm_sync_api_source/

# Copy the example project
COPY example /app/

# Install realm-sync-api from source first (with the circular import fix)
# Uninstall any existing version first, then install from source
# Then install the example project
RUN pip install --no-cache-dir --upgrade pip && \
    pip uninstall -y realm-sync-api || true && \
    pip install --no-cache-dir --force-reinstall -e /realm_sync_api_source && \
    pip install --no-cache-dir -e /app

# Expose the port
EXPOSE 8000

# Run the application
# Set PYTHONPATH to ensure the package can be imported
ENV PYTHONPATH=/app
CMD ["uvicorn", "example.main:app", "--host", "0.0.0.0", "--port", "8000"]

