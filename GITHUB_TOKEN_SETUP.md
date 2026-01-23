# GitHub Token Setup for Video Push Automation

## Why You Need a GitHub Token

The Sprite VM needs to authenticate with GitHub to push video files to your repository. A Personal Access Token (PAT) provides secure authentication.

## Quick Start

### Step 1: Create a GitHub Token

1. Go to: **https://github.com/settings/tokens**
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `Sprite Video Push Token`
4. Set expiration: `90 days` (or your preference)
5. Select scopes:
   - ✅ **`repo`** (Full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
6. Click **"Generate token"** at the bottom
7. **Copy the token immediately** (you won't see it again!)

The token will look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Set the Token as Environment Variable

```bash
export GITHUB_TOKEN='ghp_your_token_here'
```

**⚠️ Important:** Replace `ghp_your_token_here` with your actual token!

### Step 3: Run the Automated Script

```bash
./run-sprite-tests-and-push.sh
```

This will:
1. Set up the Sprite VM
2. Run UI tests with video recording
3. Convert videos to MP4
4. Commit and push to GitHub automatically

---

## Token Security Best Practices

### ✅ DO:
- Store tokens in environment variables
- Use expiring tokens (30-90 days)
- Create tokens with minimal required scopes
- Revoke tokens when done using them
- Use different tokens for different purposes

### ❌ DON'T:
- Commit tokens to git
- Share tokens publicly
- Use tokens with excessive permissions
- Leave tokens in your shell history

### Secure Token Storage

**Option 1: Shell Profile (Persistent)**
```bash
# Add to ~/.bashrc or ~/.zshrc
export GITHUB_TOKEN='ghp_your_token_here'

# Reload
source ~/.bashrc
```

**Option 2: Temporary (Current Session Only)**
```bash
# Set for current terminal session
export GITHUB_TOKEN='ghp_your_token_here'

# Verify it's set
echo $GITHUB_TOKEN | cut -c1-10
# Should show: ghp_xxxxxx
```

**Option 3: .env File (Local)**
```bash
# Create .env file (already in .gitignore)
echo "GITHUB_TOKEN=ghp_your_token_here" > .env

# Load before running script
source .env
./run-sprite-tests-and-push.sh
```

---

## Alternative: Using SSH Keys

If you prefer SSH authentication over tokens:

### Check if you have SSH keys set up

```bash
# Check if SSH keys exist
ls -la ~/.ssh/id_*.pub

# Test GitHub SSH connection
ssh -T git@github.com
```

If the test succeeds, you can modify the script to use SSH instead of HTTPS.

### Modify for SSH (in push-videos-from-sprite.sh)

Replace:
```bash
git remote set-url origin "https://oauth2:${GITHUB_TOKEN}@github.com/Adam-S-Daniel/scratch-claude-001.git"
```

With:
```bash
git remote set-url origin "git@github.com:Adam-S-Daniel/scratch-claude-001.git"
```

**Note:** The Sprite VM won't have your SSH keys, so this only works for local pushes.

---

## Troubleshooting

### "GITHUB_TOKEN not set" Error

```bash
# Check if token is set
echo $GITHUB_TOKEN

# If empty, set it:
export GITHUB_TOKEN='your_token_here'
```

### "Authentication failed" Error

Possible causes:
1. **Token expired** - Create a new token
2. **Wrong token** - Copy the token again carefully
3. **Insufficient permissions** - Token needs `repo` scope
4. **Token revoked** - Check https://github.com/settings/tokens

### "Permission denied" Error

The token needs the `repo` scope. Create a new token with correct permissions.

### Verify Token Works

```bash
# Test with curl
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Should return your GitHub user info
```

---

## Usage Examples

### Example 1: One-Time Push

```bash
# Set token (copy from GitHub)
export GITHUB_TOKEN='ghp_abc123...'

# Run automation
./run-sprite-tests-and-push.sh

# Videos will be pushed to GitHub automatically
```

### Example 2: Multiple Test Runs

```bash
# Set token once
export GITHUB_TOKEN='ghp_abc123...'

# Run multiple times (new videos each time)
./run-sprite-tests-and-push.sh
./run-sprite-tests-and-push.sh
./run-sprite-tests-and-push.sh
```

Each run creates videos with unique timestamps.

### Example 3: Using .env File

```bash
# Create .env with token
cat > .env << 'EOF'
GITHUB_TOKEN=ghp_your_token_here
EOF

# Load and run
source .env && ./run-sprite-tests-and-push.sh
```

---

## What the Script Does

When you run `./run-sprite-tests-and-push.sh`:

1. **Validates** GitHub token is set
2. **Connects** to Sprite VM (`hamhock-ui-test`)
3. **Installs** Node.js, npm, ffmpeg, Playwright
4. **Clones** your repository
5. **Runs** UI tests (desktop + mobile)
6. **Converts** WebM videos to MP4
7. **Commits** videos with timestamp
8. **Pushes** to GitHub branch: `claude/revamp-hamhock-ui-f9nXt`

**Time:** ~2-3 minutes total

**Result:** Videos appear in `test-videos/` folder on GitHub!

---

## Viewing the Videos

After the script completes:

### On GitHub
```
https://github.com/Adam-S-Daniel/scratch-claude-001/tree/claude/revamp-hamhock-ui-f9nXt/test-videos
```

### Locally
```bash
# Pull the latest changes
git pull origin claude/revamp-hamhock-ui-f9nXt

# Videos are in:
ls -lh test-videos/

# Play a video
open test-videos/desktop-ui-test-*.mp4  # macOS
xdg-open test-videos/desktop-ui-test-*.mp4  # Linux
```

---

## Token Management

### Check Active Tokens
https://github.com/settings/tokens

### Revoke When Done
After videos are pushed, you can revoke the token for security:
1. Go to: https://github.com/settings/tokens
2. Find your token
3. Click **"Delete"** or **"Revoke"**

### Regenerate if Leaked
If you accidentally commit or share a token:
1. **Immediately revoke it** on GitHub
2. Generate a new one
3. Update your environment variable

---

## FAQ

**Q: How long does the token last?**
A: You choose when creating it (30, 60, 90 days, or no expiration)

**Q: Can I reuse the same token?**
A: Yes! Set it once and reuse for multiple test runs.

**Q: Is my token secure?**
A: If you:
- Don't commit it to git ✅
- Don't share it publicly ✅
- Store in environment variables ✅
- Revoke when done ✅

**Q: What if I lose my token?**
A: Generate a new one - old ones can't be recovered.

**Q: Can others see my token in the Sprite?**
A: No, environment variables are isolated to your Sprite VM session.

---

## Summary

**To push videos from Sprite:**

```bash
# 1. Get token from GitHub
open https://github.com/settings/tokens

# 2. Set as environment variable
export GITHUB_TOKEN='ghp_your_token_here'

# 3. Run the script
./run-sprite-tests-and-push.sh

# 4. Check GitHub for videos
open https://github.com/Adam-S-Daniel/scratch-claude-001/tree/claude/revamp-hamhock-ui-f9nXt/test-videos
```

**That's it!** Videos will be automatically pushed to GitHub. 🎉
