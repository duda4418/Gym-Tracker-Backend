# Gym Tracker Backend

## Monitoring stack

This project now includes a pre-provisioned Grafana dashboard backed by Prometheus.

### Services

- Backend: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3005`

### Grafana login

Grafana reads these credentials from Compose environment variables:

- `GRAFANA_ADMIN_USER`
- `GRAFANA_ADMIN_PASSWORD`

Default values are defined in `docker-compose.yml` and mirrored in `.env.example` as `admin` / `admin`.

### Start the stack

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose up -d --build
```

### What gets provisioned automatically

- A Prometheus datasource named `Prometheus`
- A dashboard folder named `Gym Tracker`
- A starter dashboard named `Gym Tracker Overview`

### Files added for Grafana

- `grafana/provisioning/datasources/prometheus.yml`
- `grafana/provisioning/dashboards/dashboard.yml`
- `grafana/dashboards/gym-tracker-overview.json`

### Notes

- The backend already exposes Prometheus metrics at `http://localhost:8000/metrics`
- Prometheus scrapes the backend through the Compose service name `backend:8000`
- Grafana stores state in the named volume `grafana_data`

