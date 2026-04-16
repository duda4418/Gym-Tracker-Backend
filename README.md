# Gym Tracker Backend

## Monitoring stack

This project now includes:

- Prometheus for scraping metrics
- Grafana for dashboards
- Alertmanager for handling alerts triggered by Prometheus

### Services

- Backend: `http://localhost:8000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3005`
- Alertmanager: `http://localhost:9093`

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

### How the alert flow works

1. The backend exposes metrics at `/metrics`
2. Prometheus scrapes those metrics every 5 seconds
3. Prometheus evaluates rules from `prometheus/alerts.yml`
4. If a rule stays true long enough, Prometheus sends an alert to Alertmanager
5. Alertmanager groups the alert and sends it to Gmail SMTP
6. The alert is still visible in the Alertmanager UI and can also be inspected from Grafana

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

