# Stage 1: Build the React UI
FROM node:22-alpine AS ui-build
WORKDIR /app/ui
COPY ui/package.json ui/package-lock.json* ./
RUN npm ci
COPY ui/ ./
RUN npm run build

# Stage 2: Python Backend & Simulator & Grafana
FROM python:3.12-slim-bookworm
WORKDIR /app

# Install dependencies and Grafana OSS
RUN apt-get update && \
    apt-get install -y adduser libfontconfig1 wget ca-certificates && \
    wget https://dl.grafana.com/oss/release/grafana_11.1.0_amd64.deb && \
    apt-get install -y ./grafana_11.1.0_amd64.deb && \
    rm grafana_11.1.0_amd64.deb && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install the Grafana plugin (with retry for network stability)
RUN for i in 1 2 3; do grafana-cli plugins install frser-sqlite-datasource && break || sleep 5; done

# Set Grafana environment variables
ENV GF_INSTALL_PLUGINS=frser-sqlite-datasource
ENV GF_USERS_DEFAULT_THEME=light
ENV GF_AUTH_ANONYMOUS_ENABLED=true
ENV GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Copy built UI assets from Stage 1
COPY --from=ui-build /app/ui/dist /app/ui/dist

# Set Grafana provisioning and dashboards from copied files
RUN cp -r /app/grafana/provisioning/* /etc/grafana/provisioning/ || true
RUN mkdir -p /var/lib/grafana/dashboards && cp -r /app/grafana/dashboards/* /var/lib/grafana/dashboards/ || true

ENV PYTHONPATH=/app

# Make the startup script executable
RUN chmod +x /app/start.sh

# Expose ports for FastAPI (8081) and Grafana (3000)
EXPOSE 8081 3000

# Start everything via start.sh
CMD ["/app/start.sh"]
