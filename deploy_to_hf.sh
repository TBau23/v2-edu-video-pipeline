#!/bin/bash
# Deploy to HuggingFace Spaces

set -e

echo "🚀 Deploying to HuggingFace Spaces..."

# Create temp directory
TEMP_DIR="/tmp/hf-deploy-$$"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

# Clone the space
echo "📥 Cloning Space..."
git clone https://huggingface.co/spaces/tombauer/edu-video-gen
cd edu-video-gen

# Copy files
echo "📋 Copying files..."
PROJECT_ROOT="/Users/tombauer/workspace/github.com/TBau23/gauntlet/v2-education-vid-gen"

cp "$PROJECT_ROOT/app.py" .
cp "$PROJECT_ROOT/packages.txt" .
cp "$PROJECT_ROOT/requirements.txt" .
cp "$PROJECT_ROOT/README.md" .

# Copy src and examples, excluding test output and binary files
rsync -av --exclude='test_output' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='*.mp4' --exclude='*.mp3' --exclude='*.aiff' --exclude='*.wav' \
  "$PROJECT_ROOT/src/" ./src/
rsync -av --exclude='__pycache__' --exclude='*.pyc' \
  "$PROJECT_ROOT/examples/" ./examples/

# Create .gitignore to exclude unnecessary files
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
.env
venv/
*.mp4
*.mp3
projects/
.DS_Store
EOF

# Git operations
echo "📦 Committing changes..."
git add .
git commit -m "Initial deployment: Educational video generator"

echo "🔄 Pushing to HuggingFace..."
git push

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your Space: https://huggingface.co/spaces/tombauer/edu-video-gen"
echo ""
echo "⚠️  Don't forget to add your OPENAI_API_KEY in Space Settings!"
echo "   Settings → Repository secrets → New secret"
echo "   Name: OPENAI_API_KEY"
echo "   Value: your-api-key"

# Cleanup
cd /
rm -rf "$TEMP_DIR"
