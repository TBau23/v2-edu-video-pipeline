# AWS App Runner Deployment Guide

## Overview

This guide walks you through deploying the Educational Video Generator to AWS App Runner with 8GB RAM for reliable video generation.

## Prerequisites

- AWS Account with appropriate permissions
- GitHub repository connected to AWS
- OpenAI API key

## Memory Requirements ⚠️

**Critical:** This application requires **8GB RAM minimum** for reliable video generation.

- Video rendering with Manim + FFmpeg + LaTeX is memory-intensive
- Tested locally: uses 2-4GB per video generation
- 8GB provides safe headroom for complex videos

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure your repository has these files (already configured):
- ✅ `Dockerfile` - Container configuration
- ✅ `apprunner.yaml` - App Runner configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `.env.example` or environment setup

### 2. Access AWS App Runner

1. Log into AWS Console
2. Navigate to **App Runner** service
3. Click **"Create service"**

### 3. Configure Source

**Source Type:** Repository

1. **Source:** Connect to GitHub
   - First time: Authorize AWS Connector for GitHub
   - Select your repository
   - Branch: `main` (or your deployment branch)

2. **Deployment settings:**
   - ✅ Automatic deployment (optional - deploys on every push)
   - ⬜ Manual deployment (you trigger deploys)

3. **Build settings:**
   - Configuration file: Use `apprunner.yaml`
   - Or select: Docker
   - Build command: (uses Dockerfile automatically)

### 4. Configure Service

**Service name:** `educational-video-generator` (or your choice)

**CPU & Memory:** ⚠️ **IMPORTANT**
```
CPU: 2 vCPU
Memory: 8 GB    ← Critical for video rendering
```

**Port:** 7860 (Gradio default)

### 5. Configure Environment Variables

Add these environment variables in the AWS Console:

| Variable | Value | Required |
|----------|-------|----------|
| `OPENAI_API_KEY` | `sk-...` | ✅ Yes |
| `PYTHONUNBUFFERED` | `1` | ✅ Yes (already in Dockerfile) |
| `PORT` | `7860` | ✅ Yes (already in Dockerfile) |
| `RENDER_QUALITY` | `medium_quality` | ⬜ Optional (use `low_quality` for faster renders) |

**How to add environment variables:**
1. In service configuration, find "Environment variables"
2. Click "Add environment variable"
3. Enter name and value
4. Mark sensitive variables as "Secret" (like `OPENAI_API_KEY`)

### 6. Configure Health Check (Optional)

App Runner will automatically use the HEALTHCHECK in Dockerfile:
- Path: `/`
- Interval: 30 seconds
- Timeout: 10 seconds
- Healthy threshold: 1
- Unhealthy threshold: 3

### 7. Review & Deploy

1. Review all settings
2. Click **"Create & deploy"**
3. Wait 5-10 minutes for initial deployment

**Deployment progress:**
- Building image (~5 minutes)
- Deploying service (~2-3 minutes)
- Health checks (~1-2 minutes)

### 8. Access Your Application

Once deployed, App Runner provides:
- **Service URL:** `https://[random-id].awsapprunner.com`
- Copy this URL and share with your team

## Cost Estimates

AWS App Runner pricing (as of 2025):

**With auto-scaling to zero when idle:**
- **Active time:** ~$0.012/minute (~$0.72/hour)
- **Idle time:** $0 (scales to zero)
- **Typical usage:** 1-2 hours/month = ~$1-2/month

**Always-on (24/7):**
- 2 vCPU + 8GB RAM = ~$86/month

**Recommendation:** Enable auto-scaling to only pay when generating videos.

## Monitoring & Logs

### View Logs
1. Go to App Runner service
2. Click "Logs" tab
3. View real-time application logs

**What to look for:**
```
🚀 Educational Video Generator Starting...
💾 Memory: 7.5GB available / 8.0GB total
🎬 NEW VIDEO GENERATION REQUEST
Stage 1/4: Script Generation
Stage 2/4: Audio Synthesis
Stage 3/4: Visual Rendering (this may take a while)
Stage 4/4: Video Assembly
✓ Pipeline complete!
```

### Monitor Performance
- **CloudWatch Metrics** - CPU, Memory, Request count
- **Service Dashboard** - Health status, recent deployments
- **Event Log** - Deployment history, errors

## Testing Your Deployment

1. Visit your App Runner URL
2. Enter a simple test prompt:
   ```
   "Explain what 2+2 equals"
   ```
3. Watch the logs in AWS Console
4. Video should generate in 1-2 minutes

## Troubleshooting

### Issue: Service shows "Unhealthy"
**Solution:** Check logs for errors. Common causes:
- Missing `OPENAI_API_KEY` environment variable
- Port misconfiguration (ensure 7860)
- Health check failing (check Gradio is running)

### Issue: Out of Memory (OOM)
**Solution:**
- Verify you configured **8GB RAM** (not 4GB or less)
- Check CloudWatch memory metrics
- If still OOM, increase to 16GB or reduce video complexity

### Issue: Video generation times out
**Solution:**
- App Runner default timeout: 120 seconds
- Increase timeout in service settings to 300 seconds (5 minutes)
- Or use `RENDER_QUALITY=low_quality` for faster rendering

### Issue: Builds failing
**Solution:**
- Check Docker build logs in App Runner
- Verify all dependencies in `requirements.txt`
- Ensure system packages (ffmpeg, LaTeX) install correctly

### Issue: Can't see logs
**Solution:**
- Logs may take 1-2 minutes to appear
- Ensure `PYTHONUNBUFFERED=1` is set (already in Dockerfile)
- Check CloudWatch Logs directly if App Runner logs empty

## Updating Your Deployment

### Automatic Updates (if enabled):
- Push changes to your GitHub branch
- App Runner automatically rebuilds and deploys

### Manual Updates:
1. Go to App Runner service
2. Click "Deploy" → "Deploy new version"
3. Wait for deployment to complete

## Security Best Practices

1. **Environment Variables:**
   - Mark `OPENAI_API_KEY` as "Secret"
   - Never commit secrets to Git

2. **Access Control:**
   - Use IAM roles for App Runner
   - Restrict access to AWS Console

3. **Networking:**
   - App Runner provides HTTPS by default
   - Consider VPC configuration for private access

## Scaling Configuration

**Auto-scaling settings:**
- **Min instances:** 0 (scales to zero when idle)
- **Max instances:** 1 (or more for concurrent requests)
- **Concurrency:** 1 request per instance (video generation is heavy)

**Recommendation:** Keep max instances at 1 unless you need concurrent video generation.

## Alternative: AWS ECS Fargate

If you need more control, consider ECS Fargate:

**Pros:**
- More configuration options
- VPC networking
- Load balancer integration
- Spot instances (cheaper)

**Cons:**
- More complex setup
- Requires manual configuration

**Cost:** Similar to App Runner (~$0.04/hour for 2 vCPU + 8GB)

## Next Steps

After successful deployment:

1. ✅ Test with simple prompts
2. ✅ Monitor logs and performance
3. ✅ Configure auto-scaling to minimize costs
4. ✅ Share the URL with your team
5. ⬜ Set up CloudWatch alarms for errors
6. ⬜ Configure custom domain (optional)

## Support

- **AWS Documentation:** [App Runner Guide](https://docs.aws.amazon.com/apprunner/)
- **This Repository:** File an issue on GitHub
- **Logs:** Always check AWS CloudWatch Logs first

---

## Quick Reference

```bash
# Deployment checklist
☐ Repository connected to AWS
☐ Configured 8GB RAM (critical!)
☐ Added OPENAI_API_KEY environment variable
☐ Enabled auto-scaling to save costs
☐ Tested with simple prompt
☐ Verified logs are visible
☐ Shared URL with team
```

**Service URL:** (Will be provided after deployment)

**Expected Generation Time:** 1-3 minutes per video

**Memory Usage:** 2-4GB during generation

**Cost:** ~$0.012/minute when active, $0 when idle
