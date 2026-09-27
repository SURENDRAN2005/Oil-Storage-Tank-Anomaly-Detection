# Oil Storage Tank Anomaly Detection

This project is a comprehensive edge-ready application for real-time monitoring and anomaly detection of oil storage tanks. Built with a modern, high-visibility UI, a robust backend, and an embedded simulator, it's designed to track telemetry, identify leaks/anomalies, and visualize data seamlessly.

## 🚀 Features

* **Real-time Telemetry Simulator:** Continuously simulates sensor data (level, pressure, temperature, flow rates) for multiple storage tanks.
* **Intelligent Anomaly Detection:** Real-time ML/rule-based engine to flag unexpected drops in fluid levels, pressure spikes, and potential leaks.
* **Single-Container Architecture:** Completely self-contained deployment without the need for `docker-compose`. Ideal for Edge environments (like Zededa).
* **Premium React Dashboard:** A highly readable, responsive UI (React + Vite) with a clean "Modern Industrial Light" aesthetic.
* **Integrated Grafana:** Built-in Grafana instance with pre-provisioned dashboards for deep data exploration.
* **FastAPI Backend:** Lightweight and blazingly fast API to bridge the telemetry database and the user interface.

## 🏗️ Architecture Stack

* **Frontend:** React, Vite, CSS (Glassmorphism & High-Contrast Design)
* **Backend:** Python, FastAPI, SQLite (WAL mode)
* **Data Visualization:** Grafana 11.1.0
* **Deployment:** Docker (Single Image: `surendran2005/oil-storage-tank-anomaly-detection:v2.0.0`)

## ⚙️ Getting Started (Docker)

To run the entire application stack locally using Docker, simply pull and run the latest image:

```bash
# Pull the latest image
docker pull surendran2005/oil-storage-tank-anomaly-detection:v2.0.0

# Run the container with persistent data storage
docker run -d \
  --name oil-storage-app \
  -p 8081:8081 \
  -p 3000:3000 \
  -v ${PWD}/data:/app/data \
  surendran2005/oil-storage-tank-anomaly-detection:v2.0.0
```

### 🌐 Accessing the Application

Once the container is running, the services will be available at:

* **Main Dashboard:** [http://localhost:8081/dashboard](http://localhost:8081/dashboard)
* **Grafana Dashboards:** [http://localhost:3000](http://localhost:3000)

*(Note: If accessing remotely, replace `localhost` with the host machine's public IP address, and ensure firewall rules allow incoming traffic on ports `8081` and `3000`.)*

## 📁 Repository Structure

* `/ui` - React frontend source code.
* `/backend` - FastAPI server handling API requests and database interactions.
* `/simulator` - Python engine generating telemetry and evaluating anomaly rules.
* `/grafana` - Provisioning files and pre-built dashboards for Grafana.
* `start.sh` - The unified startup script executed inside the Docker container.
* `Dockerfile` - The configuration to build the single-container image.

## 🛠️ Local Development

If you wish to run the components locally without Docker:

1. **Backend & Simulator:**
   ```bash
   pip install -r requirements.txt
   python backend/main.py &
   python simulator/simulator.py &
   ```
2. **Frontend:**
   ```bash
   cd ui
   npm install
   npm run dev
   ```

## 📝 License
This project is for demonstration and educational purposes.
