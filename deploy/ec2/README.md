# EC2 backend deployment notes

This directory contains the production backend environment template used by the GitHub Actions deployment workflow in `.github/workflows/backend-deploy.yml`.

## Expected EC2 layout

The workflow expects this directory and env file on the instance:

- `/opt/gym-tracker/backend`
- `/opt/gym-tracker/backend/backend.env`

Use `backend.env.example` as the template.

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

Create the application directory and copy the env template:

```bash
sudo mkdir -p /opt/gym-tracker/backend
sudo cp backend.env.example /opt/gym-tracker/backend/backend.env
sudo chmod 600 /opt/gym-tracker/backend/backend.env
```

Then edit `/opt/gym-tracker/backend/backend.env` and set the real values for:

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

## What the workflow does

On a push to `main` or `master`, the workflow:

1. assumes the GitHub OIDC role
2. builds the Docker image from `Dockerfile`
3. pushes `<sha>` and `latest` tags to ECR
4. runs `alembic upgrade head` on the EC2 host via SSM
5. restarts the `gym-tracker-backend` container
6. verifies the container responds with `{"status": "ok"}` on `GET /`

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

