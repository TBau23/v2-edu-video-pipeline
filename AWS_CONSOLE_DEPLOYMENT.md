# AWS ECS Fargate Deployment - Console Guide

## Overview

Deploy the Educational Video Generator using the AWS Console (web interface). This guide is **easier than CLI** and visual.

**No Docker installation required!** AWS CodeBuild will build the image for you in the cloud.

**Time Required:** 45-60 minutes
**Memory:** 8GB RAM
**Cost:** ~$0.15/hour when running

---

## Prerequisites

✅ AWS Account
✅ Code pushed to GitHub
✅ OpenAI API key

**Note:** No Docker needed - AWS will build the image for you!

---

## Part 1: Build Docker Image with AWS CodeBuild (No Docker Required!)

AWS CodeBuild will build the Docker image directly from your GitHub repository.

### Step 1: Push Code to GitHub

Make sure your code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for AWS deployment"
git push origin main
```

### Step 2: Create ECR Repository

1. Go to **AWS Console** → Search for **"ECR"**
2. Click **"Create repository"**
3. Settings:
   - **Visibility:** Private
   - **Repository name:** `educational-video-generator`
   - Leave other settings as default
4. Click **"Create repository"**
5. **Copy the repository URI** (looks like: `123456789.dkr.ecr.us-east-1.amazonaws.com/educational-video-generator`)
6. **Copy your AWS Account ID** and **Region** - you'll need these

✅ **Checkpoint:** ECR repository created

### Step 3: Create buildspec.yml File

Create a file named `buildspec.yml` in your project root (if you don't have one):

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/educational-video-generator
      - IMAGE_TAG=latest
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $REPOSITORY_URI:$IMAGE_TAG .
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $REPOSITORY_URI:$IMAGE_TAG
```

**Save this file and push to GitHub:**
```bash
git add buildspec.yml
git commit -m "Add CodeBuild buildspec"
git push origin main
```

### Step 4: Create IAM Role for CodeBuild

1. Go to **AWS Console** → Search for **"IAM"**
2. Click **"Roles"** → **"Create role"**
3. **Trusted entity:** AWS service
4. **Use case:** CodeBuild
5. Click **"Next"**
6. **Add permissions** - Search and attach:
   - ✅ `AmazonEC2ContainerRegistryPowerUser` (to push to ECR)
   - ✅ `CloudWatchLogsFullAccess` (for build logs)
7. Click **"Next"**
8. **Role name:** `CodeBuildServiceRole`
9. Click **"Create role"**

✅ **Checkpoint:** CodeBuild IAM role created

### Step 5: Create CodeBuild Project

1. Go to **AWS Console** → Search for **"CodeBuild"**
2. Click **"Create project"**

**Project configuration:**
- **Project name:** `educational-video-generator-build`
- **Description:** `Build Docker image for video generator`

**Source:**
- **Source provider:** GitHub
- Click **"Connect to GitHub"** (first time only - authorizes AWS)
- **Repository:** Select your repository
- **Branch:** `main` (or your default branch)

**Environment:**
- **Environment image:** Managed image
- **Operating system:** Ubuntu
- **Runtime(s):** Standard
- **Image:** `aws/codebuild/standard:7.0` (latest)
- **Image version:** Always use the latest
- **Service role:** Existing service role
  - **Role name:** `CodeBuildServiceRole` (created in Step 4)
- **Environment variables:** Click "Add environment variable" twice:
  1. Name: `AWS_ACCOUNT_ID`, Value: `<your-account-id>`, Type: Plaintext
  2. Name: `AWS_DEFAULT_REGION`, Value: `us-east-1` (or your region), Type: Plaintext

**Buildspec:**
- **Build specifications:** Use a buildspec file
- **Buildspec name:** `buildspec.yml`

**Artifacts:**
- **Type:** No artifacts

**Logs:**
- ✅ CloudWatch logs (enabled by default)

3. Click **"Create build project"**

✅ **Checkpoint:** CodeBuild project created

### Step 6: Run the Build

1. In your CodeBuild project, click **"Start build"**
2. Leave settings as default
3. Click **"Start build"**
4. **Wait 5-10 minutes** - Watch the build logs in real-time
5. Build should complete with **"Succeeded"** status

**If build fails:**
- Check CloudWatch logs for errors
- Common issues:
  - Wrong AWS_ACCOUNT_ID or region
  - CodeBuild role missing ECR permissions
  - Dockerfile syntax errors

✅ **Checkpoint:** Docker image built and pushed to ECR

### Step 7: Verify Image in ECR

1. Go back to **ECR Console**
2. Click on `educational-video-generator` repository
3. You should see an image with tag `latest`
4. **Copy the image URI** (you'll need this for ECS task definition)

✅ **Checkpoint:** Image is in ECR and ready to deploy!

---

## Part 2: AWS Console Setup

### Step 4: Store OpenAI API Key

1. Go to **AWS Console** → Search for **"Secrets Manager"**
2. Click **"Store a new secret"**
3. Settings:
   - **Secret type:** Other type of secret
   - **Key/value pairs:**
     - Key: `OPENAI_API_KEY`
     - Value: `sk-your-actual-key-here`
   - **Encryption key:** DefaultEncryptionKey (default)
4. Click **"Next"**
5. **Secret name:** `educational-video-generator/openai-key`
6. Click **"Next"** → **"Next"** → **"Store"**
7. **Copy the Secret ARN** (looks like: `arn:aws:secretsmanager:us-east-1:123...:secret:educational...`)

✅ **Checkpoint:** Your API key is securely stored

---

### Step 5: Create IAM Role for ECS

1. Go to **AWS Console** → Search for **"IAM"**
2. Click **"Roles"** in left sidebar
3. Click **"Create role"**
4. Settings:
   - **Trusted entity type:** AWS service
   - **Use case:** Elastic Container Service → **Elastic Container Service Task**
   - Click **"Next"**
5. **Add permissions** - Search and select:
   - ✅ `AmazonECSTaskExecutionRolePolicy`
   - ✅ `SecretsManagerReadWrite`
6. Click **"Next"**
7. **Role name:** `ecsTaskExecutionRole`
8. Click **"Create role"**
9. **Copy the Role ARN** (looks like: `arn:aws:iam::123456789:role/ecsTaskExecutionRole`)

✅ **Checkpoint:** IAM role created

---

### Step 6: Create CloudWatch Log Group

1. Go to **AWS Console** → Search for **"CloudWatch"**
2. Click **"Logs"** → **"Log groups"** in left sidebar
3. Click **"Create log group"**
4. **Log group name:** `/ecs/educational-video-generator`
5. Leave other settings default
6. Click **"Create"**

✅ **Checkpoint:** Log group created

---

### Step 7: Create ECS Cluster

1. Go to **AWS Console** → Search for **"ECS"**
2. Click **"Clusters"** in left sidebar
3. Click **"Create cluster"**
4. Settings:
   - **Cluster name:** `video-generator-cluster`
   - **Infrastructure:** AWS Fargate (serverless)
   - Leave other settings default
5. Click **"Create"**

✅ **Checkpoint:** ECS cluster created

---

### Step 8: Create Task Definition

1. In **ECS Console**, click **"Task definitions"** in left sidebar
2. Click **"Create new task definition"** → **"Create new task definition"**
3. **Configure task definition:**

#### Task definition family
- **Task definition family:** `educational-video-generator`

#### Infrastructure requirements
- **Launch type:** AWS Fargate
- **Operating system:** Linux/X86_64
- **CPU:** 2 vCPU
- **Memory:** 8 GB ⚠️ **CRITICAL**
- **Task role:** None (leave empty)
- **Task execution role:** `ecsTaskExecutionRole` (created in Step 5)

#### Container - 1

Click **"Add container"**

**Container details:**
- **Name:** `video-generator`
- **Image URI:** `<YOUR_ECR_URI>:latest` (from Step 2)
- **Essential container:** Yes (checked)

**Port mappings:**
- **Container port:** `7860`
- **Protocol:** TCP
- **Port name:** `video-7860-tcp`
- **App protocol:** HTTP

**Environment variables:**

Click **"Add environment variable"** twice:

1. **Key:** `PYTHONUNBUFFERED`, **Value:** `1`
2. **Key:** `PORT`, **Value:** `7860`

**Secrets:**

Click **"Add secret"**:
- **Key:** `OPENAI_API_KEY`
- **Value type:** Secrets Manager
- **Value:** `<YOUR_SECRET_ARN>` (from Step 4)

**HealthCheck:**

Expand **"HealthCheck"** section:
- **Command:** `CMD-SHELL,curl -f http://localhost:7860/ || exit 1`
- **Interval:** `30`
- **Timeout:** `10`
- **Start period:** `60`
- **Retries:** `3`

**Logging:**

Expand **"Logging"** section:
- ✅ Use log collection
- **Log driver:** awslogs
- **Log group:** `/ecs/educational-video-generator`
- **Stream prefix:** `ecs`

Click **"Add"** (to add the container)

4. Click **"Create"** at the bottom

✅ **Checkpoint:** Task definition created

---

### Step 9: Create Security Group

1. Go to **AWS Console** → Search for **"VPC"**
2. Click **"Security Groups"** in left sidebar
3. Click **"Create security group"**
4. Settings:
   - **Security group name:** `video-generator-sg`
   - **Description:** `Security group for educational video generator`
   - **VPC:** Select your default VPC
5. **Inbound rules** - Click **"Add rule"**:
   - **Type:** Custom TCP
   - **Port range:** `7860`
   - **Source:** Anywhere-IPv4 (`0.0.0.0/0`)
   - **Description:** `Gradio web interface`
6. Leave **Outbound rules** as default (allow all)
7. Click **"Create security group"**
8. **Copy the Security Group ID** (looks like: `sg-0123456789abcdef`)

✅ **Checkpoint:** Security group created

---

### Step 10: Create ECS Service (Deploy!)

1. Go back to **ECS Console** → **"Clusters"**
2. Click on your cluster: `video-generator-cluster`
3. Click **"Create"** under Services tab
4. **Configure service:**

#### Environment
- **Compute options:** Launch type
- **Launch type:** FARGATE

#### Deployment configuration
- **Application type:** Service
- **Family:** `educational-video-generator` (select from dropdown)
- **Revision:** Latest
- **Service name:** `video-generator-service`
- **Desired tasks:** `1`

#### Networking
- **VPC:** Select your default VPC
- **Subnets:** Select at least 1 subnet (any public subnet)
- **Security group:**
  - Click "Use an existing security group"
  - Select `video-generator-sg` (created in Step 9)
- **Public IP:** ✅ **Turned on** (CRITICAL - needed to access service)

#### Load balancing (optional)
- **Load balancer type:** None (for now)

5. Click **"Create"** at the bottom

✅ **Checkpoint:** Service is deploying!

---

## Step 11: Get Your Service URL

1. Go to **ECS Console** → **Clusters** → `video-generator-cluster`
2. Click **"Tasks"** tab
3. Click on the running task (may take 2-3 minutes to appear)
4. Under **"Configuration"** section, find **"Public IP"**
5. **Your service URL:** `http://<PUBLIC_IP>:7860`

🎉 **Open that URL in your browser!**

---

## Testing

1. Open `http://<PUBLIC_IP>:7860`
2. Enter a test prompt: `"Explain what 2+2 equals"`
3. Click Submit
4. Watch the video generate (1-2 minutes)

---

## Viewing Logs

### In Console:
1. Go to **CloudWatch** → **Logs** → **Log groups**
2. Click `/ecs/educational-video-generator`
3. Click on the latest log stream
4. See your application logs in real-time!

### What logs to expect:
```
🚀 Educational Video Generator Starting...
💾 Memory: 7.5GB available / 8.0GB total
🎬 NEW VIDEO GENERATION REQUEST
Stage 1/4: Script Generation
Stage 2/4: Audio Synthesis
Stage 3/4: Visual Rendering
Stage 4/4: Video Assembly
✓ Pipeline complete!
```

---

## Cost Management

### Stop Service When Not Using (Save Money!)

1. Go to **ECS** → **Clusters** → `video-generator-cluster`
2. Click **Services** tab
3. Select `video-generator-service`
4. Click **"Update"**
5. Change **"Desired tasks"** from `1` to `0`
6. Click **"Update"**

**Cost:** $0/hour when stopped

### Start Service Again

Follow same steps but change **"Desired tasks"** back to `1`

---

## Troubleshooting

### Service won't start
1. Go to **ECS** → **Clusters** → Tasks tab
2. Click the stopped task
3. Check **"Stopped reason"** for error details

**Common issues:**
- ❌ Image not found → Check ECR URI in task definition
- ❌ Can't pull secrets → Check IAM role has SecretsManagerReadWrite
- ❌ No CPU/Memory available → Check task def has 2 vCPU + 8GB

### Can't access service
**Checklist:**
- ✅ Task is in **RUNNING** state
- ✅ Security group allows port 7860
- ✅ Public IP is enabled
- ✅ Using HTTP (not HTTPS): `http://<IP>:7860`

### Out of Memory
- Check CloudWatch logs for memory errors
- Increase memory in task definition to 16GB if needed

### Logs not appearing
- Wait 1-2 minutes after task starts
- Check log group name matches: `/ecs/educational-video-generator`
- Verify IAM role has CloudWatch permissions

---

## Updating Your Application

When you make code changes:

### 1. Rebuild and Push Image
```bash
docker build -t educational-video-generator .
docker tag educational-video-generator:latest <YOUR_ECR_URI>:latest
docker push <YOUR_ECR_URI>:latest
```

### 2. Force New Deployment (Console)
1. Go to **ECS** → **Clusters** → `video-generator-cluster`
2. Click **Services** tab → Select `video-generator-service`
3. Click **"Update"**
4. Check **"Force new deployment"**
5. Click **"Update"**

ECS will automatically pull the new image and restart.

---

## Cleanup (Remove Everything)

To stop charges and delete all resources:

1. **Delete ECS Service:**
   - ECS → Clusters → video-generator-cluster → Services
   - Select service → Actions → Delete

2. **Delete ECS Cluster:**
   - ECS → Clusters → Select cluster → Delete

3. **Delete ECR Repository:**
   - ECR → Repositories → Select → Delete

4. **Delete Secret:**
   - Secrets Manager → Select secret → Actions → Delete

5. **Delete Security Group:**
   - VPC → Security Groups → Select → Actions → Delete

6. **Delete Log Group:**
   - CloudWatch → Logs → Log groups → Select → Delete

7. **Delete IAM Role:**
   - IAM → Roles → Select ecsTaskExecutionRole → Delete

---

## Quick Reference Card

```
Service URL: http://<PUBLIC_IP>:7860
Logs: CloudWatch → /ecs/educational-video-generator
Cost: ~$0.15/hour running, $0 stopped
Memory: 8GB (critical!)
Generation Time: 1-3 minutes per video
```

---

## Next Steps

✅ Service deployed
✅ Tested with simple prompt
✅ Verified logs are visible
⬜ Set up Application Load Balancer (for custom domain)
⬜ Configure auto-scaling (for multiple users)
⬜ Set up CloudWatch alarms

---

## Need Help?

If you get stuck:
1. Check CloudWatch logs first
2. Verify all ARNs/IDs are correct
3. Check IAM permissions
4. Ask me for help with specific errors!

**Common console locations:**
- ECS: https://console.aws.amazon.com/ecs
- ECR: https://console.aws.amazon.com/ecr
- Secrets Manager: https://console.aws.amazon.com/secretsmanager
- CloudWatch: https://console.aws.amazon.com/cloudwatch
- IAM: https://console.aws.amazon.com/iam
