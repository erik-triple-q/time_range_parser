# ---- builder ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Create venv and add to PATH
RUN python -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock* README.md ./
COPY src/ src/

# Install dependencies and the package itself into the venv
RUN uv pip install --no-cache .

# ---- runtime ----
FROM python:3.12-slim AS runtime

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV TZ=Europe/Amsterdam
ENV HOST=0.0.0.0
ENV PORT=9000
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy the entrypoint script (Crucial: was missing in runtime stage)
COPY server_main.py .

EXPOSE 9000
CMD ["python", "server_main.py", "--sse"]