# Gym Tracker Backend

## Monitoring stack

This project now includes:

- Prometheus for scraping metrics
- Grafana for dashboards
- Alertmanager for handling alerts triggered by Prometheus
- OpenTelemetry tracing exported through an OpenTelemetry Collector
- Tempo for trace storage and search
- Loki for log storage and search
- Promtail for shipping backend log files into Loki
- Pyroscope for continuous profiling

### Services

- Backend: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3005`
- Alertmanager: `http://localhost:9093`
- OTel Collector health: `http://localhost:13133`
- Tempo: `http://localhost:3200`
- Loki: `http://localhost:3100`
- Pyroscope: `http://localhost:4040`

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

The backend emits OpenTelemetry traces and sends them to a local OpenTelemetry Collector.
The collector logs received traces with its built-in `debug` exporter and also forwards them to Tempo.
Backend request logs are written as structured JSON lines and shipped to Loki through Promtail.

#### What gets traced

- incoming FastAPI requests
- SQLAlchemy database calls
- outgoing `requests` calls

#### What gets logged to Loki

- backend request completion logs
- backend unhandled request errors
- trace IDs and span IDs for trace ↔ log correlation

#### Collector flow right now

1. The backend creates spans with OpenTelemetry
2. Spans are sent to the OTel Collector over OTLP/HTTP
3. The Collector batches spans
4. The Collector writes trace data to its own logs for local verification
5. The Collector forwards traces to Tempo

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
LOG_LEVEL=INFO
LOGS_DIR=app/logs
LOG_FILE_NAME=backend.log
```

Outside Docker, tracing is disabled by default.
Inside Docker Compose, the backend enables tracing automatically unless you override `OTEL_ENABLED`.

### Pyroscope profiling setup

The backend can also send continuous profiling data to Pyroscope.
This is useful for learning where Python code spends CPU time while the service is running.

#### What Pyroscope adds

- continuous CPU profiling for the backend process
- profile tags for service name, environment, and version
- a Grafana datasource for profile exploration

#### Profiling environment variables

```dotenv
PYROSCOPE_ENABLED=true
PYROSCOPE_SERVER_ADDRESS=http://pyroscope:4040
PYROSCOPE_APPLICATION_NAME=gym-tracker-backend
PYROSCOPE_SAMPLE_RATE=100
PYROSCOPE_GIL_ONLY=true
PYROSCOPE_ENABLE_LOGGING=false
```

Best-practice choice in this setup:

- profiling is opt-in
- it is enabled by default only in Docker Compose
- the Python client is imported dynamically so local host-side imports/tests stay lightweight

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
- A Tempo datasource named `Tempo`
- A Loki datasource named `Loki`
- A Pyroscope datasource named `Pyroscope`
- A dashboard folder named `Gym Tracker`
- A starter dashboard named `Gym Tracker Overview`
- Prometheus alert rules for backend availability, 5xx rate, and high latency
- An OpenTelemetry Collector that accepts OTLP traces on ports `4317` and `4318`
- Tempo trace storage on port `3200`
- Loki log storage on port `3100`
- Pyroscope profiling on port `4040`

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
- `app/core/log_config.py`
- `app/core/profiling.py`
- `otel-collector-config.yml`
- `tempo/tempo.yml`
- `loki/loki-config.yml`
- `promtail/promtail-config.yml`
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
4. The Collector forwards spans to Tempo
5. Grafana can query Tempo to inspect traces

### How the logging flow works

1. The backend writes structured JSON logs to `app/logs/backend.log`
2. Each log line includes `trace_id` and `span_id` when a trace is active
3. Promtail tails the log file and pushes entries to Loki
4. Grafana can query Loki and link log lines back to Tempo traces

### How the profiling flow works

1. The backend starts with Pyroscope profiling enabled in Docker Compose
2. The Python Pyroscope client continuously samples CPU usage in-process
3. Profiles are pushed to the Pyroscope server
4. Grafana queries Pyroscope to render flame graphs and profile views

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

Start or rebuild the backend, collector, Tempo, Loki, and Promtail:

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose up -d --build backend otel-collector tempo loki promtail grafana
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

Inspect backend logs written for Loki:

```powershell
Get-Content C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend\app\logs\backend.log -Tail 20
```

Inspect Promtail logs:

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose logs promtail --tail 100
```

Query Loki directly:

```powershell
Invoke-WebRequest -UseBasicParsing "http://localhost:3100/loki/api/v1/query?query=%7Bservice%3D%22gym-tracker-backend%22%7D" | Select-Object -ExpandProperty Content
```

If you grab a `trace_id` from one backend log line, you can also query Tempo directly:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:3200/api/traces/<trace_id> | Select-Object -ExpandProperty Content
```

In Grafana, you can now use:

- Explore → `Tempo` to browse traces
- Explore → `Loki` to browse logs
- the Loki datasource's `TraceID` derived field to jump from a log line to its Tempo trace

### How to test Pyroscope locally

Start or rebuild the backend, Pyroscope, and Grafana:

```powershell
cd C:\Users\daserban\PycharmProjects\Gym-Tracker-Backend
docker compose up -d --build backend pyroscope grafana
```

Check that Pyroscope is reachable:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:4040 | Select-Object -ExpandProperty StatusCode
```

Generate some backend activity:

```powershell
1..20 | ForEach-Object { Invoke-WebRequest -UseBasicParsing http://localhost:8000/ | Out-Null }
```

Then open Grafana and use:

- Explore → `Pyroscope`
- select the application `gym-tracker-backend`

You should start seeing CPU profile data after a short time window.

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
- Backend logs are written to `app/logs/backend.log` so Promtail can ship them reliably on local Windows/Docker setups
- Pyroscope profiling is enabled in Docker Compose and disabled by default outside Docker

## AWS backend CI/CD (`EC2` + `RDS`)

This repository now includes a production deployment workflow at `.github/workflows/backend-deploy.yml`.

On every push to `master` (and on manual `workflow_dispatch`), the workflow:

1. assumes the GitHub OIDC role `arn:aws:iam::606008290381:role/gym-tracker-backend-gha-role`
2. builds the backend Docker image from `Dockerfile`
3. tags the image with the full commit SHA and also updates `latest`
4. pushes the image to `606008290381.dkr.ecr.eu-central-1.amazonaws.com/gym-tracker-backend`
5. sends an AWS Systems Manager command to EC2 instance `i-0f68f03ec9c6a1330`
6. pulls the new image on the instance, fetches the runtime `.env` content from AWS, runs `alembic upgrade head`, stages a candidate container, switches traffic only after health checks pass, and automatically rolls back to the previous image if the final startup check fails

### Optional GitHub repository variables

The workflow has safe defaults checked into the repo, but you can override them with repository-level Actions variables:

- `AWS_REGION`
- `AWS_ROLE_ARN`
- `ECR_REPOSITORY_URI`
- `EC2_INSTANCE_ID`
- `CONTAINER_NAME`
- `REMOTE_APP_DIR`
- `HOST_PORT`
- `CONTAINER_PORT`
- `BACKEND_ENV_SSM_PARAMETER`
- `BACKEND_ENV_SECRET_ID`

If you do not set them, the workflow defaults to the current production values in AWS and exposes the backend on port `8000`.

Set exactly one of these for backend runtime configuration:

- `BACKEND_ENV_SSM_PARAMETER`: the name of an SSM Parameter Store `SecureString` containing the full dotenv payload
- `BACKEND_ENV_SECRET_ID`: the ID or ARN of a Secrets Manager secret containing the full dotenv payload

The value stored in AWS should be the full contents of `deploy/ec2/backend.env.example` with real production values filled in.

### One-time EC2 setup

Before the first deployment, the EC2 instance needs:

- Docker installed and running
- AWS CLI installed
- AWS Systems Manager Agent connected
- the EC2 instance profile with permissions to pull from ECR and receive SSM commands
- permission to read either the configured SSM parameter or Secrets Manager secret

Use `deploy/ec2/backend.env.example` as the template for the dotenv payload stored in AWS.

Important for `RDS`:

- set `POSTGRES_HOST` to `gym-tracker-prod-postgres.cna4m8i443ki.eu-central-1.amazonaws.com`
- keep `POSTGRES_PORT=5432`
- set `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` to the values configured for your RDS instance
- set a real production `JWT_SECRET_KEY`

### Deployment behavior on EC2

The deployment command writes the fetched env file here on the instance:

- `/opt/gym-tracker/backend/backend.env`

By default the workflow maps:

- host port `8000`
- container port `8000`

You can override those with the `HOST_PORT` and `CONTAINER_PORT` repository variables if the EC2 host or container image uses a different port.

It creates or reuses these Docker volumes on the instance:

- `gym-tracker-backend-logs`
- `gym-tracker-backend-uploads`

The running container name is:

- `gym-tracker-backend`

If a deploy fails after the current container has been replaced, the workflow attempts to start the previous backend image automatically.

Important migration note:

- automatic rollback restores the previous application image only
- it does **not** roll back database schema changes
- keep production migrations backward-compatible so the previous image can still run if rollback is needed

### Verifying a deployment

After the workflow succeeds, verify:

- the GitHub Actions run is green
- the new SHA tag exists in ECR
- the SSM command finished with status `Success`
- the container is running on the instance
- `http://<ec2-public-ip>:8000/` returns `{"status": "ok"}` if the security group allows direct access

### If the workflow fails before deployment starts

Most common causes are:

- the IAM role trust policy does not allow this GitHub repository to assume the OIDC role
- the EC2 instance is missing Docker, AWS CLI, or SSM connectivity
- neither `BACKEND_ENV_SSM_PARAMETER` nor `BACKEND_ENV_SECRET_ID` is configured in GitHub repository variables
- the configured parameter or secret is missing, empty, or the EC2 instance role cannot read it
- the EC2 instance profile cannot pull from the backend ECR repository

