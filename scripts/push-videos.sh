#!/bin/bash
set -e

VIDEO_DIR="test-videos"
BRANCH=$(git branch --show-current)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo "📹 Converting and pushing UI test videos to GitHub"
echo "=================================================="
echo ""
echo "Current branch: $BRANCH"
echo "Video directory: $VIDEO_DIR"
echo "Timestamp: $TIMESTAMP"
echo ""

# Check if test-results/videos exists and has videos
if [ ! -d "test-results/videos" ] || [ -z "$(ls -A test-results/videos/*.webm 2>/dev/null)" ]; then
    echo "❌ No test videos found in test-results/videos/"
    echo "   Run 'npm run test' first to generate videos"
    exit 1
fi

# Create test-videos directory if it doesn't exist
mkdir -p "$VIDEO_DIR"

# Check if ffmpeg is available
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not found. Please install ffmpeg:"
    echo "   macOS:  brew install ffmpeg"
    echo "   Ubuntu: apt-get install ffmpeg"
    echo "   Other:  https://ffmpeg.org/download.html"
    exit 1
fi

echo "🎥 Converting WebM videos to MP4..."
echo ""

# Convert each WebM video to MP4
video_count=0
for video in test-results/videos/*.webm; do
    if [ -f "$video" ]; then
        basename_no_ext=$(basename "$video" .webm)

        # Create descriptive filename
        if [[ $basename_no_ext == *"Desktop"* ]]; then
            output_name="desktop-ui-test-${TIMESTAMP}.mp4"
        elif [[ $basename_no_ext == *"Mobile"* ]]; then
            output_name="mobile-ui-test-${TIMESTAMP}.mp4"
        else
            output_name="${basename_no_ext}-${TIMESTAMP}.mp4"
        fi

        output_path="$VIDEO_DIR/$output_name"

        echo "  Converting: $(basename "$video")"
        echo "  Output: $output_name"

        # Convert with optimal settings for web
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

        echo "  ✓ Converted ($(du -h "$output_path" | cut -f1))"
        echo ""

        ((video_count++))
    fi
done

if [ $video_count -eq 0 ]; then
    echo "❌ No videos were converted"
    exit 1
fi

echo "✓ Converted $video_count video(s)"
echo ""

# List videos
echo "📹 Videos in $VIDEO_DIR/:"
ls -lh "$VIDEO_DIR"/*.mp4 2>/dev/null || echo "  No MP4 files found"
echo ""

# Git add
echo "💾 Adding videos to git..."
git add "$VIDEO_DIR"/*.mp4

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "✓ No new videos to commit (videos already in repository)"
    exit 0
fi

# Commit
echo "💾 Committing videos..."
git commit -m "Add UI test videos - $TIMESTAMP

Desktop and mobile test videos demonstrating:
- Photo-realistic 3D ham hock with Three.js
- HUGE bow tie accessory (2x scale)
- Mobile split-screen layout
- Complete game flow

Videos: $video_count file(s)
Generated: $TIMESTAMP

https://claude.ai/code/session_01ULMfLgZmVfnT9jQhp68TdW"

# Push
echo "⬆️  Pushing to GitHub..."
git push origin "$BRANCH"

echo ""
echo "✅ Videos successfully pushed!"
echo "=============================="
echo ""
echo "View on GitHub:"
echo "  https://github.com/Adam-S-Daniel/scratch-claude-001/tree/$BRANCH/$VIDEO_DIR"
echo ""
echo "Videos committed:"
for video in "$VIDEO_DIR"/*.mp4; do
    if [ -f "$video" ]; then
        echo "  - $(basename "$video")"
    fi
done
echo ""
