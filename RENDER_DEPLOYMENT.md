# Render Deployment Guide - FAILED NOT ENOUGH MEMORY

## Critical Issue: Memory Requirements ⚠️

**Problem:** This application requires **1-4GB RAM** for video rendering, but Render's **Starter plan only provides 512MB**.

### What Happens on Starter Plan:
```
Instance failed: mp6fz
Ran out of memory (used over 512MB) while running your code.
```

The app gets **OOM-killed (Out Of Memory)** during video generation, causing:
- No logs appear (process dies before completing)
- Hangs for 20-30 minutes before timeout
- "Service recovered" messages (auto-restart after crash)

## Solutions

### Option 1: Upgrade Render Plan (Recommended)
Upgrade to a plan with **at least 2GB RAM**:
- **Standard plan**: $25/mo, 2GB RAM, 1 CPU
- **Pro plan**: $85/mo, 4GB RAM, 2 CPU (best performance)

### Option 2: Use Different Platform
Platforms with better free/cheap tiers:
- **Hugging Face Spaces** (free GPU tier available)
- **Railway** ($5/mo starter with 1GB RAM)
- **Fly.io** (pay-as-you-go, ~$3-5/mo for 1GB)
- **Google Cloud Run** (generous free tier, scales to zero)

### Option 3: Run Locally (Best for Development)
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env  # Add your OPENAI_API_KEY

# 4. Run the app
python examples/web_app.py

# 5. Open browser to http://localhost:7860
```

## Current Optimizations (Already Applied)

We've already optimized the app for low-memory environments:

1. **Reduced Resolution**: 720p (1280x720) instead of 1080p
2. **Reduced FPS**: 24fps instead of 30fps
3. **Disabled Manim Caching**: Saves ~200-400MB
4. **Memory Monitoring**: Fails fast if RAM < 300MB available
5. **Unbuffered Logging**: `PYTHONUNBUFFERED=1` for immediate log visibility

**Even with these optimizations, 512MB is not enough** for Manim video rendering.

## Deployment Configuration

### Environment Variables (Set in Render Dashboard)
```bash
OPENAI_API_KEY=sk-...           # Required: Your OpenAI API key
RENDER_QUALITY=low_quality      # Optional: Use low_quality for faster renders
PYTHONUNBUFFERED=1              # Already set in Dockerfile
```

### Quality Settings
- `low_quality`: ~480p, faster rendering, less memory (still needs 1GB+)
- `medium_quality`: 720p, balanced (default)
- `high_quality`: 1080p, best quality, most memory

## Monitoring

After deploying, you should see these logs:
```
=========================================
🔍 Startup Diagnostic Check
=========================================
Python version: Python 3.11.x
RAM: 512MB
CPU cores: 1
...
🚀 Educational Video Generator Starting...
💾 Memory: 0.48GB available / 0.50GB total
⚠️ WARNING: Only 0.50GB RAM available.
Video rendering typically needs 2-4GB.
This may fail or take extremely long on limited hardware.
```

If you see the OOM warning, **video generation will likely fail**.

## Testing Locally First

Before deploying, test locally:
```bash
source venv/bin/activate
python test_logging.py  # Verify logging works
python examples/web_app.py  # Run the full app
```

Submit a test prompt like: `"Explain what 2+2 equals"` to verify it completes.

## Questions?

- **No logs showing?** Check that `PYTHONUNBUFFERED=1` is set
- **Still running out of memory?** Upgrade to a plan with 2GB+ RAM
- **Taking too long?** Set `RENDER_QUALITY=low_quality`
- **Want to run locally?** Follow Option 3 above

---

**Bottom line:** Render Starter (512MB) **will not work** for video rendering. Upgrade or use a different platform.
