#!/bin/bash
set -e

API_TOKEN="adam-761/1425148/581fa386a123b3cee5e3ad6fddfd592c/9186abb5216275aea3799b4393266cb40c23188cdebb968a5292efbb13a9daf5"
SPRITE_NAME="hamhock-ui-test"
API_BASE="https://api.sprites.dev/v1"
GAME_URL="https://adam-s-daniel.github.io/scratch-claude-001/ham-hock.html"

echo "🎬 Automated Ham Hock UI Testing on Sprites.dev"
echo "================================================"
echo ""
echo "Sprite: $SPRITE_NAME"
echo "Game URL: $GAME_URL"
echo ""

# Function to execute command in sprite and extract output
exec_sprite() {
    local cmd="$1"
    local desc="$2"

    echo "⚙️  $desc..."

    # Create temp file for response
    local response_file=$(mktemp)

    # Execute command
    curl -s -X POST "$API_BASE/sprites/$SPRITE_NAME/exec" \
      -H "Authorization: Bearer $API_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"command\":[\"bash\",\"-c\",$(printf '%s' "$cmd" | jq -Rs .)]}" \
      -o "$response_file"

    # Extract stdout/stderr, handling null bytes
    local output=$(cat "$response_file" | tr -d '\000' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    stdout = data.get('stdout', '')
    stderr = data.get('stderr', '')
    exit_code = data.get('exit_code', 0)
    if stderr:
        print(f'[stderr] {stderr}', file=sys.stderr)
    if stdout:
        print(stdout)
    sys.exit(exit_code)
except Exception as e:
    print(f'Error parsing response: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

    local exit_code=$?

    # Clean up temp file
    rm -f "$response_file"

    # Print output
    echo "$output"

    if [ $exit_code -ne 0 ]; then
        echo "❌ Command failed with exit code $exit_code"
        return $exit_code
    fi

    echo "✓ Done"
    echo ""

    return 0
}

# Wait for GitHub Pages deployment
echo "⏳ Waiting for GitHub Pages deployment..."
echo "Checking $GAME_URL"
echo ""

for i in {1..30}; do
    if curl -s -I "$GAME_URL" | head -1 | grep -q "200"; then
        echo "✓ GitHub Pages is live!"
        echo ""
        break
    fi
    echo "  Attempt $i/30: Not ready yet, waiting 5s..."
    sleep 5
done

# Check one more time
if ! curl -s -I "$GAME_URL" | head -1 | grep -q "200"; then
    echo "❌ GitHub Pages not accessible after 150s"
    exit 1
fi

# Install system dependencies
exec_sprite "apt-get update -qq && apt-get install -y curl git 2>&1 | tail -5" "Installing system dependencies"

# Install Node.js
exec_sprite "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1 && apt-get install -y nodejs 2>&1 | tail -3" "Installing Node.js 20"

# Verify Node.js
exec_sprite "node --version && npm --version" "Verifying Node.js installation"

# Clone repository
exec_sprite "cd /tmp && rm -rf scratch-claude-001 && git clone -q https://github.com/Adam-S-Daniel/scratch-claude-001.git 2>&1" "Cloning repository"

# Checkout branch
exec_sprite "cd /tmp/scratch-claude-001 && git checkout claude/revamp-hamhock-ui-f9nXt 2>&1 | tail -2" "Checking out branch"

# Install dependencies
exec_sprite "cd /tmp/scratch-claude-001 && npm install 2>&1 | tail -5" "Installing npm dependencies"

# Install Playwright
exec_sprite "cd /tmp/scratch-claude-001 && npx playwright install --with-deps chromium 2>&1 | tail -10" "Installing Playwright + Chromium"

# Run tests
echo "🎬 Running Playwright UI tests..."
echo "This will take ~60 seconds..."
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && timeout 120 npm run test 2>&1" "Running UI tests"

# Check test results
echo ""
echo "📊 Test Results:"
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && cat test-results/.last-run.json 2>/dev/null | python3 -c \"import sys,json;d=json.load(sys.stdin);print(f\\\"Tests: {d.get('stats',{}).get('expected',0)} passed\\\")\" 2>/dev/null || echo 'Results file not found'" "Checking test results"

# List generated videos
echo ""
echo "📹 Generated Videos:"
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && find test-results/videos -name '*.webm' 2>/dev/null | while read f; do ls -lh \"\$f\"; done" "Listing video files"

# Get video count
exec_sprite "cd /tmp/scratch-claude-001 && find test-results/videos -name '*.webm' 2>/dev/null | wc -l" "Counting videos"

# List screenshots
echo ""
echo "📸 Generated Screenshots:"
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && find screenshots -name '*.png' 2>/dev/null | head -10" "Listing screenshots"

# Try to get a snippet of test output
echo ""
echo "📝 Test Output Preview:"
echo ""

exec_sprite "cd /tmp/scratch-claude-001 && tail -50 test-results/.last-run.json 2>/dev/null || echo 'No test output available'" "Getting test output"

echo ""
echo "✅ Automated testing complete!"
echo "================================"
echo ""
echo "Sprite VM Details:"
echo "  Name: $SPRITE_NAME"
echo "  URL: https://hamhock-ui-test-blpx4.sprites.app"
echo ""
echo "Videos Location: /tmp/scratch-claude-001/test-results/videos/"
echo ""
echo "To access the Sprite and download videos:"
echo "  sprite console $SPRITE_NAME"
echo "  cd /tmp/scratch-claude-001/test-results/videos"
echo "  ls -lh"
echo ""
echo "To download a video:"
echo "  # Inside sprite console:"
echo "  python3 -m http.server 8000"
echo "  # Then access: http://localhost:8000/test-results/videos/"
echo ""
