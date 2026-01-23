# Quick Start: Push Videos from Sprite to GitHub

## ✅ The Fix is Ready!

The Sprite can now properly push videos to GitHub. Here's how to use it:

## 3-Step Process

### Step 1: Get a GitHub Token (2 minutes)

1. Visit: **https://github.com/settings/tokens**
2. Click **"Generate new token (classic)"**
3. Name it: `Video Push Token`
4. Select scope: **✅ repo** (full control)
5. Click **"Generate token"**
6. **Copy the token** (starts with `ghp_`)

### Step 2: Set the Token (10 seconds)

```bash
export GITHUB_TOKEN='ghp_paste_your_token_here'
```

### Step 3: Run the Script (2-3 minutes)

```bash
./run-sprite-tests-and-push.sh
```

**That's it!** The script will:
- ✅ Run UI tests on Sprite VM
- ✅ Convert videos to MP4
- ✅ Push to GitHub automatically

## What You'll Get

After ~2-3 minutes, videos will be on GitHub:

**Desktop video:**
- `test-videos/desktop-ui-test-TIMESTAMP.mp4`
- 1920x1080, ~35 seconds
- Shows all features including HUGE bow tie

**Mobile video:**
- `test-videos/mobile-ui-test-TIMESTAMP.mp4`
- 375x667, ~15 seconds
- Shows mobile layout and button fix

## View Videos

**On GitHub:**
```
https://github.com/Adam-S-Daniel/scratch-claude-001/tree/claude/revamp-hamhock-ui-f9nXt/test-videos
```

**Locally:**
```bash
git pull origin claude/revamp-hamhock-ui-f9nXt
ls -lh test-videos/
```

## Full Documentation

For detailed instructions, security tips, and troubleshooting:
- See: **`GITHUB_TOKEN_SETUP.md`**

## Alternative: Run Tests Locally

If you prefer to run tests locally instead of on Sprite:

```bash
npm install
npx playwright install chromium
npm run test:push
```

This will:
- Run tests locally
- Convert videos
- Push to GitHub

## What Happens on the Sprite

The automation does this automatically:

1. **Setup** - Installs Node.js, npm, ffmpeg, Playwright
2. **Clone** - Gets latest code from GitHub
3. **Test** - Runs full UI test suite (~60 seconds)
4. **Convert** - WebM → MP4 with optimal settings
5. **Commit** - Adds videos with timestamp
6. **Push** - Uploads to GitHub with your token

## Expected Output

```
🎬 Running UI Tests on Sprite and Pushing to GitHub
====================================================

✓ GitHub token provided
Sprite: hamhock-ui-test
Branch: claude/revamp-hamhock-ui-f9nXt

⏳ Step 1: Setting up Sprite environment...
⚙️  Installing dependencies...
✓ Done

⏳ Step 2: Cloning repository and installing...
⚙️  Cloning repository...
✓ Done

⏳ Step 3: Running UI tests (this takes ~60 seconds)...
⚙️  Running Playwright tests...
✓ Done

⏳ Step 4: Converting and pushing videos...
⚙️  Converting and pushing videos...
✓ Done

✅ Process complete!
===================

Check GitHub for videos:
  https://github.com/Adam-S-Daniel/scratch-claude-001/tree/claude/revamp-hamhock-ui-f9nXt/test-videos
```

## Troubleshooting

### "GITHUB_TOKEN not set" Error
```bash
# Make sure you exported it:
export GITHUB_TOKEN='ghp_your_token'

# Verify it's set:
echo $GITHUB_TOKEN | cut -c1-10
# Should show: ghp_xxxxxx
```

### "Authentication failed"
- Token might be wrong - copy it again
- Token might need `repo` scope - check permissions
- Token might be expired - generate new one

### Videos Not Appearing
```bash
# Wait a moment, then pull:
git pull origin claude/revamp-hamhock-ui-f9nXt

# Check test-videos folder:
ls -lh test-videos/
```

## Security Note

Your token is:
- ✅ Only used inside the Sprite VM
- ✅ Not stored anywhere permanently
- ✅ Only valid for pushes to your repo
- ✅ Can be revoked anytime

After videos are pushed, you can revoke the token at:
https://github.com/settings/tokens

---

## Summary

**To push videos from Sprite right now:**

```bash
# 1. Get token (one time)
open https://github.com/settings/tokens

# 2. Set token
export GITHUB_TOKEN='ghp_your_token_here'

# 3. Run script
./run-sprite-tests-and-push.sh

# Done! Videos on GitHub in 2-3 minutes
```

**Need help?** See `GITHUB_TOKEN_SETUP.md` for detailed guide.
