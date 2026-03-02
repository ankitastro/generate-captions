# Kundali Engine Service Deployment Guide

This guide explains how to deploy and manage the kundali-engine service on AWS ECS Fargate.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Docker installed and running
- Terraform installed
- Access to ECR and ECS

## Quick Start

### Full Deployment Workflow

Deploy everything in one command:

```bash
make -f Makefile.service all
```

This will:
1. Build the Docker image
2. Push it to ECR
3. Deploy/update the ECS service via Terraform
4. Display service status

### Quick Deployment (Image Already Built)

If the image is already built and pushed:

```bash
make -f Makefile.service quick-deploy
```

## Step-by-Step Usage

### 1. Build Docker Image

```bash
make -f Makefile.service build
```

This builds the kundali-engine service from `Dockerfile`.

### 2. Push to ECR

```bash
make -f Makefile.service push
```

This will automatically login to ECR before pushing.

### 3. Deploy with Terraform

```bash
make -f Makefile.service terraform-init    # First time only
make -f Makefile.service terraform-apply   # Deploy/update service
```

Or use the combined deploy command:

```bash
make -f Makefile.service deploy
```

### 4. Check Service Status

```bash
make -f Makefile.service status
```

Shows:
- Service name, status, desired/running/pending task counts
- Task health status
- Current deployment status

### 5. View Logs

```bash
make -f Makefile.service logs
```

Streams CloudWatch logs from the last 5 minutes.

### 6. Restart Service

Force a new deployment (restart all tasks):

```bash
make -f Makefile.service restart
```

### 7. Scale Service

```bash
make -f Makefile.service scale DESIRED_COUNT=5
```

Scales the service to the specified number of tasks (within auto-scaling limits: 2-10).

## Available Commands

| Command | Description |
|---------|-------------|
| `make -f Makefile.service help` | Show all available commands |
| `make -f Makefile.service build` | Build Docker image |
| `make -f Makefile.service ecr-login` | Login to AWS ECR |
| `make -f Makefile.service push` | Push image to ECR |
| `make -f Makefile.service terraform-init` | Initialize Terraform |
| `make -f Makefile.service terraform-plan` | Plan Terraform changes |
| `make -f Makefile.service terraform-apply` | Deploy/update service |
| `make -f Makefile.service deploy` | Push image and deploy |
| `make -f Makefile.service logs` | View service logs |
| `make -f Makefile.service status` | Check service status |
| `make -f Makefile.service restart` | Force new deployment |
| `make -f Makefile.service scale DESIRED_COUNT=N` | Scale service |
| `make -f Makefile.service destroy` | Destroy service |
| `make -f Makefile.service clean` | Clean local images |
| `make -f Makefile.service all` | Full workflow |
| `make -f Makefile.service quick-deploy` | Quick deployment |
| `make -f Makefile.service update-image` | Rebuild and push image |

## Configuration

The Makefile uses these default values (can be overridden):

```bash
AWS_REGION=ap-south-1
AWS_ACCOUNT_ID=135808951138
IMAGE_TAG=latest
ECS_CLUSTER=astrokiran-fargate-spot-cluster
SERVICE_NAME=kundali-engine
```

To override:

```bash
make -f Makefile.service IMAGE_TAG=v1.2.3 push
```

## Service Architecture

### ECS Configuration
- **Cluster**: `astrokiran-fargate-spot-cluster`
- **Service**: `kundali-engine`
- **Task Definition**: `kundali-engine:latest`
- **CPU**: 256
- **Memory**: 512 MB
- **Desired Count**: 2 tasks
- **Launch Type**: FARGATE (70% Spot / 30% On-Demand)

### Auto Scaling
- **Min Tasks**: 2
- **Max Tasks**: 10
- **CPU Target**: 70%
- **Memory Target**: 80%

### Networking
- **VPC**: `vpc-04f751f7682013a31`
- **Subnets**: 3 public subnets across AZs
- **Security Group**: `sg-05a16d13a178fff0f`
- **Public IP**: Enabled

### Service Discovery
- **Namespace**: `askapp-services.local`
- **Service DNS**: `kundali-engine.askapp-services.local`
- **Type**: Cloud Map (AWS Service Discovery)
- **Access**: Internal VPC only

### Application Configuration
- **Port**: 9090
- **Framework**: FastAPI (Python)
- **Health Check**: `/api/v1/kundali/health`
- **API Docs**: `/docs` (Swagger UI)

## Environment Variables

The service is deployed with these environment variables:

- `ENVIRONMENT=production`
- `PORT=9090`

## Deployment Workflow

### Development to Production

1. **Make code changes** in `kundali-engine/`
2. **Build and test locally** (optional)
3. **Build and push image**:
   ```bash
   make -f Makefile.service build push
   ```
4. **Deploy to ECS**:
   ```bash
   make -f Makefile.service terraform-apply
   ```
5. **Monitor deployment**:
   ```bash
   make -f Makefile.service status
   make -f Makefile.service logs
   ```

### Rolling Updates

ECS performs rolling updates automatically:
- **Deployment Strategy**: Rolling update
- **Max Healthy %**: 200%
- **Min Healthy %**: 100%

This means during deployment:
- New tasks start before old tasks stop
- Zero downtime
- If new tasks fail health checks, rollback occurs

### Rollback

If deployment fails:

1. **Check logs**:
   ```bash
   make -f Makefile.service logs
   ```

2. **Manual rollback** (if needed):
   ```bash
   # Revert to previous task definition
   aws ecs update-service \
     --cluster astrokiran-fargate-spot-cluster \
     --service kundali-engine \
     --task-definition kundali-engine:1 \
     --region ap-south-1
   ```

## Monitoring & Debugging

### View Logs
```bash
# Continuous logs (last 5 minutes, follow mode)
make -f Makefile.service logs

# Or use AWS CLI directly
aws logs tail /ecs/kundali-engine --follow --region ap-south-1
```

### Check Service Health
```bash
# Service status
make -f Makefile.service status

# Test health endpoint (from within VPC)
curl http://kundali-engine.askapp-services.local:9090/api/v1/kundali/health
```

### Debug Task Issues
```bash
# List running tasks
aws ecs list-tasks \
  --cluster astrokiran-fargate-spot-cluster \
  --service-name kundali-engine \
  --region ap-south-1

# Describe specific task
aws ecs describe-tasks \
  --cluster astrokiran-fargate-spot-cluster \
  --tasks <task-arn> \
  --region ap-south-1
```

### Connect to Task (ECS Exec)
```bash
# Get task ARN
TASK_ARN=$(aws ecs list-tasks \
  --cluster astrokiran-fargate-spot-cluster \
  --service-name kundali-engine \
  --region ap-south-1 \
  --query 'taskArns[0]' \
  --output text)

# Execute command
aws ecs execute-command \
  --cluster astrokiran-fargate-spot-cluster \
  --task $TASK_ARN \
  --container kundali-engine \
  --interactive \
  --command "/bin/sh" \
  --region ap-south-1
```

## Troubleshooting

### Issue: Image not found

**Solution**: Build and push the image first
```bash
make -f Makefile.service build push
```

### Issue: Service deployment stuck

**Possible causes**:
- Health check failing (check logs)
- Insufficient resources (check task stopped reason)
- Network issues (check security group)

**Debug**:
```bash
make -f Makefile.service logs
make -f Makefile.service status
```

### Issue: Tasks keep restarting

**Check**:
1. Application logs for errors
2. Health check endpoint (`/api/v1/kundali/health`)
3. Environment variables
4. Dependencies (ephemeris files, libraries)

### Issue: Health check 404 errors

The health endpoint is at `/api/v1/kundali/health` (not `/health`).

Verify the task definition has the correct health check path:
```bash
aws ecs describe-task-definition \
  --task-definition kundali-engine \
  --region ap-south-1 \
  --query 'taskDefinition.containerDefinitions[0].healthCheck'
```

## Service Discovery Access

The kundali-engine service is accessible within the VPC at:

```
http://kundali-engine.askapp-services.local:9090
```

### Example API Calls (from within VPC)

```bash
# Health check
curl http://kundali-engine.askapp-services.local:9090/api/v1/kundali/health

# API documentation
curl http://kundali-engine.askapp-services.local:9090/docs

# Generate Kundali
curl -X POST http://kundali-engine.askapp-services.local:9090/api/v1/kundali/generate-kundali \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## API Endpoints

Key endpoints available:
- `GET /api/v1/kundali/health` - Health check
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `POST /api/v1/kundali/generate-kundali` - Generate birth chart
- `POST /api/v1/kundali/kundali-matching` - Compatibility matching
- See full API documentation at `/docs` when service is running

## CI/CD Integration

To integrate with CI/CD:

```yaml
# Example GitHub Actions
- name: Deploy kundali-engine
  run: |
    cd kundali-engine
    make -f Makefile.service build
    make -f Makefile.service push
    make -f Makefile.service terraform-apply

    # Verify deployment
    make -f Makefile.service status
```

## Cleanup

To destroy the service:

```bash
make -f Makefile.service destroy
```

**Warning**: This will delete:
- ECS service and tasks
- Task definitions
- IAM roles
- CloudWatch log groups
- Service Discovery service

The Cloud Map namespace is managed by alpha-service and will NOT be deleted.

## Replacing Alpha Service

This service replaces the alpha-service:
- **alpha-service** has been scaled to 0 tasks
- **kundali-engine** now handles all Vedic astrology requests
- Both services use the same Cloud Map namespace (`askapp-services.local`)

## Additional Resources

- [Dockerfile](./Dockerfile) - Service Docker image
- [terraform/](./terraform/) - Infrastructure as Code
- [CLAUDE.md](./CLAUDE.md) - Development guide
- [API_README.md](./API_README.md) - API documentation
