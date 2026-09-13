# ☀️ Solar Park Monitoring: IoT Supervision of a Photovoltaic Solar Park

## 📖 Project Description
This project is a miniature, autonomous industrial supervision system (SCADA) designed to monitor the real-time production of a photovoltaic park. Based on an Edge Computing architecture, it collects environmental data via physical sensors, calculates the generated electrical power, and exposes these metrics on dynamic dashboards. The entire software infrastructure is containerized, ensuring a resilient, reproducible operation completely isolated from public Cloud services.

## ⚙️ System Operation
The system relies on a fluid telemetry pipeline operating on a local network:

1. **Physical Acquisition:** Sensors (LDR) measure the direct sunshine level. These analog data are read and processed continuously by an ESP32 microcontroller.
2. **Wireless Transmission:** The ESP32 publishes these readings on the local Wi-Fi network via the MQTT IoT protocol. The frames are received by a containerized Mosquitto broker.
3. **Processing and Conversion:** A gateway service developed in Python listens to the MQTT broker. It applies conversion formulas to transform raw brightness into an estimated power output (Watts) for each panel and calculates total production.
4. **Database:** The Prometheus engine continuously queries (scrapes) this Python service to store the metric history in the form of time series.
5. **Visual Supervision:** The Grafana interface connects to Prometheus to dynamically update control interfaces (individual power curves and global production gauge).


## 💻​ Running the Project

This project requires (To be checked directly with the owner: **+261 34 37 020 61**): 

- A Hardware system
- A Network configuration

For the Software part, launching the project is already automated via Makefile and Docker:

- `make` (or `make all` / `make run`): Compiles and runs Docker containers in the background by activating `DOCKER_BUILDKIT` and rebuilding images if necessary.
- `make build`: Forces the construction (or complete rebuilding without using the cache) of the Docker images defined in the configuration file.
- `make down`: Stops and removes the currently running project containers.
- `make clean`: Stops the containers and removes associated volumes (clearing persistent data).
- `make fclean`: Performs a complete cleanup (`clean`) while additionally purging all system containers, networks, and Docker images (`docker system prune -a --volumes`).
- `make re`: Fully restarts the project from scratch by first executing a complete cleanup (`fclean`) followed by a new build and execution (`all`).