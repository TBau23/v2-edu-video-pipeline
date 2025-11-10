# Hugging Face Spaces Deployment Guide

**Goal**: Deploy the video generator to Hugging Face Spaces for **FREE** hosting.

**Result**: Public URL like `https://huggingface.co/spaces/yourusername/edu-video-gen`

---

## Why Hugging Face Spaces?

✅ **FREE** hosting (no credit card needed)
✅ Built specifically for Gradio apps
✅ Auto-deploys from Git
✅ Gives you a public URL instantly
✅ No Docker knowledge needed

⚠️ **Limitations**:
- Public (anyone can see/use it)
- Limited CPU (videos take longer ~5-10 min)
- 50GB storage limit
- Sleeps after inactivity (wakes on first request)

For this use case (simple demo, low traffic), it's perfect!

---

## Prerequisites

1. **Hugging Face Account**: https://huggingface.co/join (free, 2 minutes)
2. **OpenAI API Key**: Get from https://platform.openai.com/api-keys
3. **Code ready**: Pipeline must work locally first (complete E2E-004)

---

## Deployment Steps (10 minutes)

### Step 1: Create a Space

1. Go to https://huggingface.co/new-space
2. Fill out form:
   - **Owner**: Your username
   - **Space name**: `edu-video-gen` (or whatever you want)
   - **License**: MIT
   - **Select SDK**: **Gradio** ← Important!
   - **Hardware**: CPU basic (free)
   - **Visibility**: Public (free) or Private (Pro account needed)
3. Click **Create Space**

### Step 2: Prepare Files

HuggingFace Spaces needs specific files in the repo root:

**Required files**:
```
app.py                    ← Entry point (will create this)
requirements.txt          ← Python dependencies (already exists)
README.md                 ← Space description (will create this)
```

**Your code structure**:
```
src/                      ← Your pipeline code
examples/web_app.py       ← The Gradio app we created
.env.example              ← Template for environment variables
```

### Step 3: Create `app.py` (HF Entry Point)

HuggingFace Spaces looks for `app.py` in the root. We'll just import our existing web_app:

```python
# app.py (create in project root)
"""
Hugging Face Spaces entry point.
This file is required by HF Spaces - it just launches our web app.
"""

# Import and run the web app
from examples.web_app import demo

# Launch (HF Spaces will handle the server)
demo.launch()
```

Create this file:
```bash
cat > app.py << 'EOF'
from examples.web_app import demo
demo.launch()
EOF
```

### Step 4: Create Space README

HuggingFace uses README.md for the Space description. Create this in project root:

```markdown
---
title: Educational Video Generator
emoji: 🎓
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# 🎓 AI Educational Video Generator

Generate educational videos from text prompts using AI.

## How it works

1. **Enter a topic**: Describe what you want explained
2. **AI generates**: Script, narration, equations, and animations
3. **Get video**: Download or watch in browser

## Examples

- "Explain Newton's First Law with a car example"
- "What is the Pythagorean theorem?"
- "Describe photosynthesis with diagrams"

## Tech Stack

- **Script**: OpenAI GPT-4
- **Audio**: OpenAI TTS
- **Visuals**: Manim (mathematics animation engine)
- **Assembly**: FFmpeg

## Note

Video generation takes 3-5 minutes. Please be patient!
```

### Step 5: Add OpenAI API Key (Secret)

1. In your Space settings, go to **Settings** → **Repository secrets**
2. Click **New secret**
3. Name: `OPENAI_API_KEY`
4. Value: Your OpenAI API key
5. Click **Save**

### Step 6: Push Code to Space

HuggingFace Spaces uses Git. Two options:

**Option A: Upload via Web UI** (easiest)
1. In your Space, click **Files** → **Add file** → **Upload files**
2. Upload all necessary files:
   - `app.py`
   - `requirements.txt`
   - Entire `src/` directory
   - Entire `examples/` directory
   - `README.md` (Space description)
3. Click **Commit changes**

**Option B: Git Push** (if you prefer terminal)
```bash
# Clone the Space
git clone https://huggingface.co/spaces/yourusername/edu-video-gen
cd edu-video-gen

# Copy your files
cp -r /path/to/your/project/src .
cp -r /path/to/your/project/examples .
cp /path/to/your/project/requirements.txt .
cp /path/to/your/project/app.py .

# Commit and push
git add .
git commit -m "Initial deployment"
git push
```

### Step 7: Wait for Build

1. HuggingFace will automatically build your Space
2. Watch the **Logs** tab to see progress
3. Build takes 5-10 minutes (installs dependencies)
4. When done, you'll see: **"Running on local URL: http://0.0.0.0:7860"**

### Step 8: Test Your Space

1. Your Space is now live at: `https://huggingface.co/spaces/yourusername/edu-video-gen`
2. Test by entering a prompt
3. Wait 3-5 minutes for video generation
4. Share the URL with anyone!

---

## Troubleshooting

### Space shows "Error: OPENAI_API_KEY not configured"
→ Add the secret in Space settings (Step 5)

### Space shows "Building..." forever
→ Check **Logs** tab for errors
→ Common issues:
  - Missing dependency in requirements.txt
  - LaTeX not installed (see Fix #1 below)

### Video generation fails
→ Check **Logs** tab for specific error
→ Common issues:
  - LaTeX missing (see Fix #1)
  - FFmpeg missing (see Fix #2)
  - Out of memory (see Fix #3)

### Space sleeps after inactivity
→ This is normal for free tier
→ First request after sleep will wake it up (takes ~30s)
→ Upgrade to "always on" for $9/month if needed

---

## Fixes for Common Issues

### Fix #1: LaTeX Not Installed

HuggingFace Spaces doesn't include LaTeX by default. Create `packages.txt`:

```bash
# packages.txt (in project root)
texlive-latex-base
texlive-fonts-recommended
texlive-latex-extra
```

Then commit and push this file.

### Fix #2: FFmpeg Not Installed

Add to `packages.txt`:
```bash
# packages.txt
ffmpeg
```

### Fix #3: Out of Memory

Free tier has limited RAM. If videos fail to render:

**Option 1**: Reduce quality settings in code
```python
# In web_app.py
pipeline = VideoPipeline(workspace, quality="low_quality")
```

**Option 2**: Upgrade to better hardware
- Go to Space settings
- Change **Hardware** to "CPU upgrade" (~$0.60/hour when running)

### Fix #4: Slow Performance

Free CPU is slow. Videos take 5-10 minutes instead of 3-5.

**Solutions**:
- Accept slower performance (it's free!)
- Upgrade hardware to CPU upgrade ($0.60/hour)
- Set clear expectations in UI ("This may take 5-10 minutes")

---

## Updating Your Space

When you make code changes:

```bash
cd edu-video-gen
# Make changes to files
git add .
git commit -m "Update: description of changes"
git push
```

Space will automatically rebuild and redeploy.

---

## Making Space Private

Free Spaces are public. To make private:

1. Upgrade to HuggingFace Pro ($9/month)
2. Go to Space settings
3. Change visibility to **Private**

---

## Cost Breakdown

**Hosting**: $0 (free tier)
**OpenAI API**: ~$0.15 per video
  - Script generation: ~$0.05
  - Audio synthesis: ~$0.10

**Total**: Pay only for API usage, no hosting fees!

---

## Alternative: Deploy to Railway Instead

If you want better performance and don't mind paying $5/month:

1. Create Railway account: https://railway.app
2. New Project → Deploy from GitHub
3. Add environment variable: `OPENAI_API_KEY`
4. Railway auto-detects Dockerfile and deploys
5. Get URL: `your-app.up.railway.app`

Performance is much better (videos in 3-5 min instead of 5-10 min).

---

## Summary

**Hugging Face Spaces**:
- ✅ FREE
- ✅ Easy setup (10 minutes)
- ✅ Public URL
- ⚠️ Slower performance
- ⚠️ Public by default

**Railway**:
- 💰 $5-20/month
- ✅ Fast performance
- ✅ Private by default
- ✅ Better for "production" use

For a demo or low-traffic use, **Hugging Face Spaces is perfect!**

---

## Next Steps

1. ✅ Complete E2E-004 (pipeline orchestrator)
2. ✅ Test locally: `python examples/web_app.py`
3. ✅ Create HuggingFace Space
4. ✅ Upload files
5. ✅ Add API key secret
6. ✅ Test deployed Space
7. ✅ Share URL!

You'll have a working public URL in under an hour.
