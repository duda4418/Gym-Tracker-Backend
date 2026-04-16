# Gym Tracker Backend

## Monitoring stack

This project now includes:

- Prometheus for scraping metrics
- Grafana for dashboards
- Alertmanager for handling alerts triggered by Prometheus
- OpenTelemetry tracing exported through an OpenTelemetry Collector

### Services

- Backend: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3005`
- Alertmanager: `http://localhost:9093`
- OTel Collector health: `http://localhost:13133`

### What Alertmanager is for

Prometheus detects problems by evaluating alert rules.
Alertmanager receives those alerts and helps you:

- group duplicate alerts
- delay noisy alerts until they persist for some time
- silence alerts during maintenance
- route alerts to different destinations later (email, Slack, Discord, webhook, PagerDuty, etc.)

In this project, Alertmanager is the layer that sits between Prometheus and any human notification channel.
It is now configured to send email alerts through Gmail SMTP, while also keeping alerts visible in the Alertmanager UI and accessible from Grafana.

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

### OpenTelemetry tracing setup

The backend now emits OpenTelemetry traces and sends them to a local OpenTelemetry Collector.
For now, the collector only logs received traces with its built-in `debug` exporter.
This keeps the setup simple until Tempo and Loki are added later.

#### What gets traced

- incoming FastAPI requests
- SQLAlchemy database calls
- outgoing `requests` calls

#### Collector flow right now

1. The backend creates spans with OpenTelemetry
2. Spans are sent to the OTel Collector over OTLP/HTTP
3. The Collector batches spans
4. The Collector writes trace data to its own logs for local verification

#### Tracing environment variables

These variables are available for local customization:

```dotenv
OTEL_ENABLED=true
OTEL_SERVICE_NAME=gym-tracker-backend
OTEL_SERVICE_VERSION=1.0.0
OTEL_ENVIRONMENT=docker
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://otel-collector:4318/v1/traces
OTEL_EXPORTER_TIMEOUT_SECONDS=10
OTEL_TRACES_SAMPLER_RATIO=1.0
```

Outside Docker, tracing is disabled by default.
Inside Docker Compose, the backend enables tracing automatically unless you override `OTEL_ENABLED`.

### Gmail email alerting setup

Alertmanager is wired to send alerts to:

- `dudadud4418@gmail.com`

The file `alertmanager.yml` acts as a template.
At container startup, `alertmanager-entrypoint.sh` injects the SMTP values from environment variables and starts Alertmanager with the rendered config.

To make Gmail accept SMTP sends from Alertmanager, you must use a Gmail App Password.
Your normal Gmail login password will not work here.

#### 1. Create a Gmail App Password

For the Gmail account you want to send from:

1. Enable Google 2-Step Verification
2. Open Google Account → Security → App passwords
3. Create a new App Password
4. Copy the generated 16-character password

#### 2. Put the SMTP values in your `.env`

Add these variables to your local `.env` file:

```dotenv
ALERTMANAGER_SMARTHOST=smtp.gmail.com:587
ALERTMANAGER_EMAIL_FROM=dudadud4418@gmail.com
ALERTMANAGER_EMAIL_TO=dudadud4418@gmail.com
ALERTMANAGER_AUTH_USERNAME=dudadud4418@gmail.com
ALERTMANAGER_AUTH_PASSWORD=your-16-character-gmail-app-password
```

Important:

- `ALERTMANAGER_EMAIL_FROM` should usually match the authenticated Gmail account
- `ALERTMANAGER_AUTH_USERNAME` should also usually be the same Gmail address
- do not commit the real app password to Git

#### 3. Restart Alertmanager after changing `.env`

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose up -d alertmanager
```

### What gets provisioned automatically

- A Prometheus datasource named `Prometheus`
- An Alertmanager datasource named `Alertmanager`
- A dashboard folder named `Gym Tracker`
- A starter dashboard named `Gym Tracker Overview`
- Prometheus alert rules for backend availability, 5xx rate, and high latency
- An OpenTelemetry Collector that accepts OTLP traces on ports `4317` and `4318`

### Files added for Grafana

- `grafana/provisioning/datasources/prometheus.yml`
- `grafana/provisioning/dashboards/dashboard.yml`
- `grafana/dashboards/gym-tracker-overview.json`

### Files for Alertmanager

- `alertmanager.yml`
- `alertmanager-entrypoint.sh`
- `prometheus.yml`
- `prometheus/alerts.yml`
- `docker-compose.yml`
- `.env.example`

### Files for OpenTelemetry

- `app/core/telemetry.py`
- `otel-collector-config.yml`
- `docker-compose.yml`
- `requirements.txt`

### How the alert flow works

1. The backend exposes metrics at `/metrics`
2. Prometheus scrapes those metrics every 5 seconds
3. Prometheus evaluates rules from `prometheus/alerts.yml`
4. If a rule stays true long enough, Prometheus sends an alert to Alertmanager
5. Alertmanager groups the alert and sends it to Gmail SMTP
6. The alert is still visible in the Alertmanager UI and can also be inspected from Grafana

### How the tracing flow works

1. FastAPI starts with optional OpenTelemetry instrumentation
2. Each request creates a trace with spans for the API layer and database work
3. The backend exports spans to the OTel Collector
4. The Collector logs those spans locally for verification
5. Later, the same Collector can forward traces to Tempo and logs to Loki

### Starter alerts included

- `BackendDown`: the backend cannot be scraped for 1 minute
- `High5xxRate`: the backend returns too many 5xx responses for 5 minutes
- `HighP95Latency`: p95 latency stays above 750ms for 10 minutes

### How to test Alertmanager locally

Start the stack:

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose up -d --build
```

Open these pages:

- Prometheus targets: `http://localhost:9090/targets`
- Prometheus alerts: `http://localhost:9090/alerts`
- Alertmanager alerts: `http://localhost:9093/#/alerts`

Easy test ideas:

1. Stop the backend container and wait about 1 minute:

```powershell
docker compose stop backend
```

2. Check Alertmanager and Prometheus to see the `BackendDown` alert fire.
3. Check the inbox for `dudadud4418@gmail.com`.
4. If the mail is not in Inbox, also check Spam.
5. Start the backend again:

```powershell
docker compose start backend
```

If the email does not arrive, inspect the Alertmanager logs:

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose logs alertmanager --tail 100
```

### How to test OpenTelemetry locally

Start or rebuild the backend and collector:

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose up -d --build backend otel-collector
```

Check collector health:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:13133 | Select-Object -ExpandProperty Content
```

Generate a traced request:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:8000/
```

Inspect collector logs for received spans:

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose logs otel-collector --tail 100
```

You should see spans for the backend service in the collector logs.

### Gmail troubleshooting tips

- Gmail SMTP host: `smtp.gmail.com:587`
- TLS is required
- use an App Password, not your normal Gmail password
- the sender address should match the authenticated Gmail account
- if Google blocks login, recreate the App Password and restart Alertmanager

### Next step: more notification channels

Once you are comfortable with the local flow, you can extend `alertmanager.yml` with a real receiver such as:

- email (SMTP)
- Slack
- Discord webhook
- generic webhook

### Notes

- The backend already exposes Prometheus metrics at `http://localhost:8000/metrics`
- Prometheus scrapes the backend through the Compose service name `backend:8000`
- Grafana stores state in the named volume `grafana_data`
- Alertmanager uses Gmail SMTP settings passed through container environment variables
- OpenTelemetry traces are enabled in Docker Compose and disabled by default outside Docker

