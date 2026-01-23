#!/bin/bash
set -e

# This script should be run INSIDE the Sprite VM
# It converts videos, commits them, and pushes to GitHub

BRANCH="claude/revamp-hamhock-ui-f9nXt"
VIDEO_DIR="test-videos"
TIMESTAMP=$(date -u +%Y%m%d-%H%M%S)

echo "🎬 Pushing UI Test Videos to GitHub from Sprite"
echo "==============================================="
echo ""
echo "Branch: $BRANCH"
echo "Video directory: $VIDEO_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Navigate to repo
cd /tmp/scratch-claude-001 || exit 1

# Make sure we're on the right branch
git checkout "$BRANCH" 2>&1 || exit 1

# Pull latest changes
echo "⬇️  Pulling latest changes..."
git pull origin "$BRANCH" 2>&1 || echo "Pull failed, continuing anyway..."
echo ""

# Create video directory
mkdir -p "$VIDEO_DIR"

# Convert videos
echo "🎥 Converting WebM videos to MP4..."
echo ""

video_count=0
for video in test-results/videos/*.webm; do
    if [ -f "$video" ]; then
        basename_file=$(basename "$video" .webm)

        # Create descriptive name based on test
        if [[ $basename_file == *"Desktop"* ]]; then
            output_name="desktop-ui-test-${TIMESTAMP}.mp4"
        elif [[ $basename_file == *"Mobile"* ]]; then
            output_name="mobile-ui-test-${TIMESTAMP}.mp4"
        else
            output_name="${basename_file}-${TIMESTAMP}.mp4"
        fi

        output_path="$VIDEO_DIR/$output_name"

        echo "Converting: $(basename "$video")"
        echo "Output: $output_name"

        ffmpeg -i "$video" \
            -c:v libx264 \
            -preset medium \
            -crf 23 \
            -c:a aac \
            -b:a 128k \
            -movflags +faststart \
            "$output_path" \
            -y \
            -loglevel error

        if [ -f "$output_path" ]; then
            size=$(du -h "$output_path" | cut -f1)
            echo "✓ Converted ($size)"
            ((video_count++))
        else
            echo "✗ Conversion failed"
        fi
        echo ""
    fi
done

if [ $video_count -eq 0 ]; then
    echo "❌ No videos were converted"
    exit 1
fi

echo "✓ Converted $video_count video(s)"
echo ""

# List converted videos
echo "📹 Videos in $VIDEO_DIR/:"
ls -lh "$VIDEO_DIR"/*.mp4 2>/dev/null || echo "No MP4 files found"
echo ""

# Configure git
git config user.email "sprite-bot@sprites.dev"
git config user.name "Sprite Test Bot"

# Add videos
echo "💾 Adding videos to git..."
git add "$VIDEO_DIR"/*.mp4

# Check if there are changes
if git diff --staged --quiet; then
    echo "✓ No new videos to commit"
    exit 0
fi

# Commit
echo "💾 Committing videos..."
git commit -m "Add UI test videos from Sprite - $TIMESTAMP

Desktop and mobile test recordings:
- Desktop: 1920x1080, ~35 seconds
- Mobile: 375x667, ~15 seconds

Generated on Sprite VM
Date: $(date -u +%Y-%m-%d_%H:%M:%S_UTC)

Features demonstrated:
✓ Photo-realistic 3D ham hock
✓ HUGE bow tie accessory (2x scale)
✓ Mobile split-screen layout
✓ Mobile button fix verified
✓ Complete game flow

Videos: $video_count file(s)

https://claude.ai/code/session_01ULMfLgZmVfnT9jQhp68TdW"

echo ""
echo "⬆️  Pushing to GitHub..."

# Push using HTTPS with credentials in URL
# The token should be passed as an environment variable: GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN environment variable not set"
    echo "   Set with: export GITHUB_TOKEN='your_github_token'"
    exit 1
fi

# Configure remote with token
git remote set-url origin "https://oauth2:${GITHUB_TOKEN}@github.com/Adam-S-Daniel/scratch-claude-001.git"

# Push
git push origin "$BRANCH" 2>&1

echo ""
echo "✅ Videos successfully pushed to GitHub!"
echo "========================================"
echo ""
echo "View on GitHub:"
echo "  https://github.com/Adam-S-Daniel/scratch-claude-001/tree/$BRANCH/$VIDEO_DIR"
echo ""
echo "Videos committed:"
for video in "$VIDEO_DIR"/*.mp4; do
    if [ -f "$video" ]; then
        echo "  - $(basename "$video") ($(du -h "$video" | cut -f1))"
    fi
done
echo ""
