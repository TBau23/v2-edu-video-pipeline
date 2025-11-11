#!/bin/bash
#
# ECS Fargate Deployment Helper Script
# Automates the deployment of Educational Video Generator to AWS ECS
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_REGION="us-east-1"
REPO_NAME="educational-video-generator"
CLUSTER_NAME="video-generator-cluster"
SERVICE_NAME="video-generator-service"
TASK_FAMILY="educational-video-generator"

echo "========================================"
echo "🚀 ECS Fargate Deployment Script"
echo "========================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo -e "${RED}✗ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install it first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Get AWS region
read -p "AWS Region [$DEFAULT_REGION]: " AWS_REGION
AWS_REGION=${AWS_REGION:-$DEFAULT_REGION}

# Get AWS account ID
echo "Getting AWS account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ Account ID: $AWS_ACCOUNT_ID${NC}"
echo ""

# Get OpenAI API key
read -sp "Enter your OpenAI API key: " OPENAI_API_KEY
echo ""

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}✗ OpenAI API key is required${NC}"
    exit 1
fi

echo ""
echo "========================================"
echo "Step 1/8: Creating ECR Repository"
echo "========================================"

ECR_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME"

if aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION &> /dev/null; then
    echo -e "${YELLOW}⚠ Repository already exists, skipping...${NC}"
else
    aws ecr create-repository \
        --repository-name $REPO_NAME \
        --region $AWS_REGION \
        --query 'repository.repositoryUri' \
        --output text
    echo -e "${GREEN}✓ ECR repository created${NC}"
fi

echo ""
echo "========================================"
echo "Step 2/8: Building and Pushing Docker Image"
echo "========================================"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $ECR_REPO

# Build image
echo "Building Docker image..."
docker build -t $REPO_NAME .

# Tag and push
echo "Tagging and pushing image..."
docker tag $REPO_NAME:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

echo -e "${GREEN}✓ Docker image pushed to ECR${NC}"

echo ""
echo "========================================"
echo "Step 3/8: Storing OpenAI API Key in Secrets Manager"
echo "========================================"

SECRET_NAME="$REPO_NAME/openai-key"

if aws secretsmanager describe-secret --secret-id $SECRET_NAME --region $AWS_REGION &> /dev/null; then
    echo -e "${YELLOW}⚠ Secret already exists, updating...${NC}"
    aws secretsmanager update-secret \
        --secret-id $SECRET_NAME \
        --secret-string "{\"OPENAI_API_KEY\":\"$OPENAI_API_KEY\"}" \
        --region $AWS_REGION > /dev/null
else
    aws secretsmanager create-secret \
        --name $SECRET_NAME \
        --secret-string "{\"OPENAI_API_KEY\":\"$OPENAI_API_KEY\"}" \
        --region $AWS_REGION > /dev/null
fi

SECRET_ARN=$(aws secretsmanager describe-secret --secret-id $SECRET_NAME --region $AWS_REGION --query ARN --output text)
echo -e "${GREEN}✓ Secret stored: $SECRET_ARN${NC}"

echo ""
echo "========================================"
echo "Step 4/8: Creating IAM Roles"
echo "========================================"

# Create trust policy
cat > /tmp/ecs-task-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

ROLE_NAME="ecsTaskExecutionRole"

if aws iam get-role --role-name $ROLE_NAME &> /dev/null; then
    echo -e "${YELLOW}⚠ IAM role already exists, skipping...${NC}"
else
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/ecs-task-trust-policy.json > /dev/null

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite

    echo -e "${GREEN}✓ IAM role created${NC}"
fi

EXECUTION_ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME"

echo ""
echo "========================================"
echo "Step 5/8: Creating CloudWatch Log Group"
echo "========================================"

LOG_GROUP="/ecs/$REPO_NAME"

if aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP --region $AWS_REGION | grep -q $LOG_GROUP; then
    echo -e "${YELLOW}⚠ Log group already exists, skipping...${NC}"
else
    aws logs create-log-group \
        --log-group-name $LOG_GROUP \
        --region $AWS_REGION
    echo -e "${GREEN}✓ Log group created${NC}"
fi

echo ""
echo "========================================"
echo "Step 6/8: Registering Task Definition"
echo "========================================"

# Update task definition with actual values
cat > /tmp/task-definition.json <<EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "8192",
  "executionRoleArn": "$EXECUTION_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "video-generator",
      "image": "$ECR_REPO:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 7860,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PYTHONUNBUFFERED",
          "value": "1"
        },
        {
          "name": "PORT",
          "value": "7860"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "$SECRET_ARN"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "$LOG_GROUP",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:7860/ || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-definition.json \
    --region $AWS_REGION > /dev/null

echo -e "${GREEN}✓ Task definition registered${NC}"

echo ""
echo "========================================"
echo "Step 7/8: Creating ECS Cluster"
echo "========================================"

if aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION | grep -q ACTIVE; then
    echo -e "${YELLOW}⚠ Cluster already exists, skipping...${NC}"
else
    aws ecs create-cluster \
        --cluster-name $CLUSTER_NAME \
        --region $AWS_REGION > /dev/null
    echo -e "${GREEN}✓ ECS cluster created${NC}"
fi

echo ""
echo "========================================"
echo "Step 8/8: Creating ECS Service"
echo "========================================"

# Get default VPC and subnet
echo "Getting default VPC configuration..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION)
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[0].SubnetId' --output text --region $AWS_REGION)

# Create or get security group
SG_NAME="video-generator-sg"
if SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SG_NAME" --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION 2>/dev/null) && [ "$SG_ID" != "None" ]; then
    echo -e "${YELLOW}⚠ Security group already exists${NC}"
else
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SG_NAME \
        --description "Security group for video generator" \
        --vpc-id $VPC_ID \
        --region $AWS_REGION \
        --query 'GroupId' \
        --output text)

    # Allow inbound traffic on port 7860
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 7860 \
        --cidr 0.0.0.0/0 \
        --region $AWS_REGION > /dev/null || true

    echo -e "${GREEN}✓ Security group created${NC}"
fi

# Check if service exists
if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION | grep -q ACTIVE; then
    echo -e "${YELLOW}⚠ Service already exists, updating...${NC}"
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --force-new-deployment \
        --region $AWS_REGION > /dev/null
    echo -e "${GREEN}✓ Service updated${NC}"
else
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
        --region $AWS_REGION > /dev/null
    echo -e "${GREEN}✓ Service created${NC}"
fi

echo ""
echo "========================================"
echo "✅ Deployment Complete!"
echo "========================================"
echo ""
echo "Waiting for service to stabilize (this may take 2-3 minutes)..."
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo ""
echo "Getting service URL..."
TASK_ARN=$(aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'taskArns[0]' \
    --output text)

if [ "$TASK_ARN" != "None" ] && [ -n "$TASK_ARN" ]; then
    ENI_ID=$(aws ecs describe-tasks \
        --cluster $CLUSTER_NAME \
        --tasks $TASK_ARN \
        --region $AWS_REGION \
        --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' \
        --output text)

    PUBLIC_IP=$(aws ec2 describe-network-interfaces \
        --network-interface-ids $ENI_ID \
        --region $AWS_REGION \
        --query 'NetworkInterfaces[0].Association.PublicIp' \
        --output text)

    echo ""
    echo "========================================"
    echo "🎉 Your service is deployed!"
    echo "========================================"
    echo ""
    echo "Service URL: http://$PUBLIC_IP:7860"
    echo ""
    echo "View logs:"
    echo "  aws logs tail $LOG_GROUP --follow --region $AWS_REGION"
    echo ""
    echo "Scale to zero when not in use:"
    echo "  aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --desired-count 0 --region $AWS_REGION"
    echo ""
else
    echo -e "${YELLOW}⚠ Task not running yet. Check status:${NC}"
    echo "  aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION"
fi

# Cleanup temp files
rm -f /tmp/ecs-task-trust-policy.json /tmp/task-definition.json

echo "========================================"
