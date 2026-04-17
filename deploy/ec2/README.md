# EC2 backend deployment notes

This directory contains the production backend environment template used by the GitHub Actions deployment workflow in `.github/workflows/backend-deploy.yml`.

## Expected EC2 layout

The workflow creates or refreshes this directory and env file on the instance during deployment:

- `/opt/gym-tracker/backend`
- `/opt/gym-tracker/backend/backend.env`

Use `backend.env.example` as the template for the dotenv content stored in AWS.

## One-time EC2 setup

Install Docker, make sure AWS CLI is available, and confirm the instance is managed by AWS Systems Manager.

Example commands for Ubuntu:

```bash
sudo apt update
sudo apt install -y docker.io awscli
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

Create the application directory:

```bash
sudo mkdir -p /opt/gym-tracker/backend
```

Store the full dotenv payload from `backend.env.example` in one of these AWS locations:

- an SSM Parameter Store `SecureString`
- a Secrets Manager secret

Then set exactly one GitHub Actions repository variable:

- `BACKEND_ENV_SSM_PARAMETER`
- `BACKEND_ENV_SECRET_ID`

The stored dotenv content must contain real values for:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `JWT_SECRET_KEY`

## IAM expectations

### GitHub Actions role

The GitHub OIDC role must be able to:

- push images to the backend ECR repository
- send SSM commands to the EC2 instance
- read SSM command results

### EC2 instance profile

The EC2 instance profile should have at least:

- `AmazonSSMManagedInstanceCore`
- `AmazonEC2ContainerRegistryReadOnly`
- `ssm:GetParameter` if you use Parameter Store
- `secretsmanager:GetSecretValue` if you use Secrets Manager
- `kms:Decrypt` if your parameter or secret uses a customer-managed KMS key

## What the workflow does

On a push to `master`, the workflow:

1. assumes the GitHub OIDC role
2. builds the Docker image from `Dockerfile`
3. pushes `<sha>` and `latest` tags to ECR
4. fetches the full backend dotenv payload from SSM Parameter Store or Secrets Manager and writes it atomically to `/opt/gym-tracker/backend/backend.env`
5. runs `alembic upgrade head` on the EC2 host via SSM
6. starts a candidate container and health-checks it before replacing the live container
7. attempts to roll back to the previous image automatically if the final startup check fails

## Optional GitHub Actions repository variables

You can override the built-in defaults with these repository variables:

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

Set exactly one of `BACKEND_ENV_SSM_PARAMETER` or `BACKEND_ENV_SECRET_ID`.

## Rollback behavior

The workflow keeps the previous backend image reference before it replaces the running container.
If the final production container fails its startup or `GET /` health check, the workflow attempts to start the previous image automatically.

This rollback only restores the application image.
It does not revert database schema changes made by `alembic upgrade head`, so production migrations should stay backward-compatible.

## Manual verification after a deployment

Useful EC2 checks:

```bash
docker ps
docker logs --tail 100 gym-tracker-backend
curl http://127.0.0.1:8000/
```

If the instance security group exposes the backend port, you can also test externally:

```bash
curl http://<ec2-public-ip>:8000/
```

