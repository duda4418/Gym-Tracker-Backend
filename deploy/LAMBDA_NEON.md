# Lambda and Neon deployment

## Runtime configuration

Use the Neon **pooled** connection string for the Lambda `DATABASE_URL`. Its
hostname contains `-pooler` and the URL should end with:

```text
?sslmode=require&channel_binding=require
```

Recommended Lambda environment values:

```dotenv
DATABASE_POOL_SIZE=1
DATABASE_MAX_OVERFLOW=0
DATABASE_POOL_RECYCLE_SECONDS=300
POSTGRES_CONNECT_TIMEOUT_SECONDS=5
POSTGRES_POOL_TIMEOUT_SECONDS=5
LOG_TO_FILE=false
CORS_ORIGINS=https://your-production-site.vercel.app,http://localhost:3000
OTEL_ENABLED=false
PYROSCOPE_ENABLED=false
```

Store `DATABASE_URL` and `JWT_SECRET_KEY` in a secret store. Do not commit them
or put plaintext values in Terraform state. The Lambda handler is
`app.main.handler`.

Keep the Lambda outside a VPC unless it needs private resources. A Lambda in a
private subnet needs NAT egress to reach Neon's public endpoint. Start with a
30-second timeout, 512 MB memory, and reserved concurrency of 5 to bound initial
database concurrency. Raise concurrency only after observing latency and Neon
connection metrics.

FastAPI owns CORS in this application. Leave Function URL CORS disabled to
avoid duplicate headers, and set `CORS_ORIGINS` to exact Vercel production and
preview origins that should be trusted.

## Neon configuration

- Use a primary read-write compute on the main branch.
- Keep the project in `eu-central-1`, matching the Lambda region.
- Use the smallest compute initially and keep scale to zero enabled for low
  traffic. The first request after an idle period can have additional latency.
- Use the pooled endpoint for Lambda traffic.
- Use the direct endpoint for Alembic, `pg_dump`, and `pg_restore`.
- If IP Allow is enabled, Lambda needs stable NAT egress addresses. Otherwise,
  leave IP restrictions disabled and rely on TLS, a strong database password,
  and least-privilege database roles.
- Monitor compute usage, storage, pooler client connections, pooler server
  connections, and slow queries in the Neon console.

## RDS migration

The current RDS hostname is private, so run the transfer from the existing EC2
instance through SSM. Before starting, store the new Neon **direct** connection
URL in Secrets Manager or an SSM `SecureString`; do not pass it as an SSM command
argument.

1. Deploy this code against RDS so `alembic upgrade head` adds the QR binary
   columns.
2. Import persisted QR files while the EC2 uploads volume is mounted:

   ```bash
   docker run --rm \
     --env-file /opt/gym-tracker/backend/backend.env \
     -v /opt/gym-tracker/backend/app/uploads:/app/app/uploads:ro \
     <backend-image> \
     python -m app.scripts.import_qr_codes
   ```

3. Use PostgreSQL 17 or the same major version as the Neon target to dump RDS
   in custom format. Use RDS environment values without printing them:

   ```bash
   docker run --rm \
     --env-file /opt/gym-tracker/backend/backend.env \
     -v /opt/gym-tracker/backend:/backup \
     postgres:17-alpine sh -c \
     'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
       --host="$POSTGRES_HOST" --port="$POSTGRES_PORT" \
       --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" \
       --format=custom --no-owner --no-acl \
       --file=/backup/gym-tracker.dump'
   ```

4. Verify the Neon target is empty, then restore using the direct URL retrieved
   from the secret store:

   ```bash
   docker run --rm \
     -e TARGET_DATABASE_URL \
     -v /opt/gym-tracker/backend:/backup:ro \
     postgres:17-alpine sh -c \
     'pg_restore --exit-on-error --no-owner --no-acl \
       --dbname="$TARGET_DATABASE_URL" \
       /backup/gym-tracker.dump'
   ```

5. Run `alembic current`, compare table row counts between RDS and Neon, test
   login/refresh, splits, workouts, favorites, and QR retrieval, then switch the
   Lambda `DATABASE_URL` to the pooled Neon URL.

Do not delete RDS until the Neon backup and application checks have passed.

## QR frontend behavior

`GET /users/get-qr` still returns `qr_code_url`, now set to
`/users/qr-image`. The image endpoint requires the same bearer token as the
other user endpoints. The frontend should fetch it with the authorization
header, create a browser object URL from the returned blob, and revoke the
object URL when it is no longer needed.