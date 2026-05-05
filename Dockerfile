FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .
COPY __init__.py .

EXPOSE 8000

# Run MCP server via stdio (standard MCP transport)
CMD ["python", "server.py"]
