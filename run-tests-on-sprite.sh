#!/bin/bash

API_TOKEN="adam-761/1425148/581fa386a123b3cee5e3ad6fddfd592c/9186abb5216275aea3799b4393266cb40c23188cdebb968a5292efbb13a9daf5"
SPRITE_NAME="hamhock-ui-test"
API_BASE="https://api.sprites.dev/v1"

echo "🎬 Running Ham Hock UI Tests on Sprites.dev"
echo "==========================================="
echo ""

# Function to execute command in sprite
exec_cmd() {
    local cmd="$1"
    local desc="$2"
    echo "⚙️  $desc..."

    local response=$(curl -s -X POST "$API_BASE/sprites/$SPRITE_NAME/exec" \
      -H "Authorization: Bearer $API_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"command\":[\"bash\",\"-c\",\"$cmd\"]}")

    echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('stdout', ''), data.get('stderr', ''), sep='')" 2>/dev/null || echo "$response"
    echo ""
}

# Install Node.js
exec_cmd "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>&1 && apt-get install -y nodejs 2>&1 | tail -5" "Installing Node.js"

# Install Git
exec_cmd "apt-get install -y git 2>&1 | tail -3" "Installing Git"

# Clone repository
exec_cmd "cd /tmp && git clone https://github.com/Adam-S-Daniel/scratch-claude-001.git 2>&1" "Cloning repository"

# Checkout branch
exec_cmd "cd /tmp/scratch-claude-001 && git checkout claude/revamp-hamhock-ui-f9nXt 2>&1" "Checking out test branch"

# Install npm dependencies
exec_cmd "cd /tmp/scratch-claude-001 && npm install 2>&1 | tail -10" "Installing npm dependencies"

# Install Playwright
exec_cmd "cd /tmp/scratch-claude-001 && npx playwright install --with-deps chromium 2>&1 | tail -20" "Installing Playwright and Chromium"

# Run tests
exec_cmd "cd /tmp/scratch-claude-001 && npm run test 2>&1" "Running Playwright UI tests"

# List generated videos
exec_cmd "cd /tmp/scratch-claude-001 && ls -lh test-results/videos/ 2>&1" "Listing generated videos"

echo ""
echo "✅ Tests complete!"
echo "Videos are in: /tmp/scratch-claude-001/test-results/videos/"
echo ""
echo "To access the Sprite:"
echo "  Sprite Name: $SPRITE_NAME"
echo "  Sprite URL: https://hamhock-ui-test-blpx4.sprites.app"
