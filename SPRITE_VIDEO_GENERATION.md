# Generate UI Test Videos on Sprite

## Quick Start (3 Steps)

### 1. Get a GitHub Token (2 minutes)

1. Visit: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: `Video Push Token`
4. Scope: ✅ **repo** (full control)
5. Click "Generate token"
6. Copy the token (starts with `ghp_`)

### 2. Set Environment Variables

```bash
export GITHUB_TOKEN='ghp_your_token_here'
```

### 3. Run the Script

```bash
./sprite-generate-and-push.sh
```

**That's it!** The script runs everything on the Sprite VM:
- Installs dependencies
- Clones repository
- Runs UI tests (~60 seconds)
- Converts videos to MP4
- Pushes to GitHub automatically

Takes 3-5 minutes total.

---

## What It Does

The script executes on the Sprite VM in a single command using `sprite exec`:

### Workflow Steps:

1. **Install Dependencies**
   - curl, git, ffmpeg
   - Node.js & npm
   - Playwright + Chromium

2. **Clone Repository**
   - Clones from GitHub
   - Checks out `claude/revamp-hamhock-ui-f9nXt` branch

3. **Install Project Dependencies**
   - `npm install` (packages from package.json)
   - `npx playwright install --with-deps chromium`

4. **Run UI Tests**
   - Executes Playwright test suite
   - Records desktop video (1920x1080)
   - Records mobile video (375x667)
   - Videos saved as WebM in `test-results/videos/`

5. **Convert Videos**
   - Converts WebM to MP4 using ffmpeg
   - Desktop → `desktop-ui-test-TIMESTAMP.mp4`
   - Mobile → `mobile-ui-test-TIMESTAMP.mp4`
   - Saves to `test-videos/` folder

6. **Commit to Git**
   - Configures git user (Sprite Test Bot)
   - Adds MP4 files
   - Creates commit with timestamp

7. **Push to GitHub**
   - Uses OAuth2 token authentication
   - Pushes to branch: `claude/revamp-hamhock-ui-f9nXt`

---

## View Results

### On GitHub

After ~3-5 minutes, videos will be at:

```
https://github.com/Adam-S-Daniel/scratch-claude-001/tree/claude/revamp-hamhock-ui-f9nXt/test-videos
```

### Locally

Pull the latest changes:

```bash
git pull origin claude/revamp-hamhock-ui-f9nXt
ls -lh test-videos/
```

---

## Video Content

### Desktop Video (~35 seconds)
- Photo-realistic 3D ham hock rendering
- Size selection tests
- Color selection tests
- **HUGE bow tie accessory** (2x scale) ⭐
- Other accessories
- Seasoning selection
- Complete game flow

### Mobile Video (~15 seconds)
- Mobile layout (split-screen)
- **Button click working** (bug fix verified) ⭐
- Ham hock + options both visible
- No page scrolling required
- BOW TIE rendering on mobile

---

## How It Works

### The Script (`sprite-generate-and-push.sh`)

Uses **`sprite exec`** command from Sprites CLI:

```bash
sprite exec "$SPRITE_SCRIPT"
```

This command:
- **Blocks until completion** - waits for entire workflow
- **Returns output** - shows all stdout/stderr
- **Reports exit code** - success or failure

### Benefits of `sprite exec`

✅ **Simple** - Single command execution
✅ **Reliable** - Waits for completion
✅ **Transparent** - See all output
✅ **No API complexity** - CLI handles authentication

---

## Prerequisites

### Required:

1. **Sprites CLI installed**
   ```bash
   npm install -g @sprites.dev/cli
   ```

2. **Logged into Sprite**
   ```bash
   sprite login
   ```

3. **GitHub Token with `repo` scope**
   - See setup instructions above

### The Sprite:

- **Name:** `hamhock-ui-test`
- Should already exist and be accessible
- Script uses this specific sprite name

---

## Troubleshooting

### "GITHUB_TOKEN not set"

```bash
# Set the token:
export GITHUB_TOKEN='ghp_your_token'

# Verify it's set:
echo $GITHUB_TOKEN | cut -c1-10
# Should show: ghp_xxxxxx
```

### "sprite: command not found"

Install Sprites CLI:
```bash
npm install -g @sprites.dev/cli
sprite login
```

### "Authentication failed" (GitHub)

- Token expired - generate a new one
- Missing `repo` scope - recreate with correct permissions
- Token copied incorrectly - copy again

### Videos Not Appearing

Wait a moment, then:
```bash
git pull origin claude/revamp-hamhock-ui-f9nXt
ls -lh test-videos/
```

Check the script output for errors.

### Script Timeout

If the script takes too long, check:
- Network connection to Sprite
- Sprite VM is running
- GitHub is accessible from Sprite

---

## Security Notes

### GitHub Token:

- ✅ Only used inside Sprite VM
- ✅ Not stored permanently
- ✅ Only for pushes to your repo
- ✅ Can be revoked anytime

### After Videos Are Pushed:

Revoke the token at: https://github.com/settings/tokens

### Never:

- ❌ Commit tokens to git
- ❌ Share tokens publicly
- ❌ Use tokens with excessive permissions

---

## Full Command Reference

### Complete Workflow:

```bash
# 1. Set token
export GITHUB_TOKEN='ghp_your_token_here'

# 2. Run script
./sprite-generate-and-push.sh

# 3. Wait 3-5 minutes

# 4. Pull videos
git pull origin claude/revamp-hamhock-ui-f9nXt

# 5. View locally
ls -lh test-videos/
open test-videos/desktop-*.mp4  # macOS
xdg-open test-videos/desktop-*.mp4  # Linux
```

### Multiple Runs:

Each run creates new videos with unique timestamps:

```bash
# Run 1
./sprite-generate-and-push.sh
# → desktop-ui-test-20260123-120000.mp4

# Run 2
./sprite-generate-and-push.sh
# → desktop-ui-test-20260123-120330.mp4

# etc.
```

---

## Expected Output

When you run the script, you'll see:

```
🎬 Generating Videos on Sprite VM and Pushing to GitHub
=======================================================

This will run everything in a single command on the Sprite
Sprite: hamhock-ui-test
Branch: claude/revamp-hamhock-ui-f9nXt

📝 Executing script on Sprite VM...
   This will take 3-5 minutes to complete

===== STEP 1: Install Dependencies =====
✓ Dependencies installed

===== STEP 2: Clone Repository =====
✓ Repository cloned and checked out

===== STEP 3: Install Node Packages =====
✓ npm packages installed

===== STEP 4: Install Playwright =====
✓ Playwright installed

===== STEP 5: Run Tests (takes ~60 seconds) =====
Running 2 tests...
✓ Desktop UI Test (35s)
✓ Mobile UI Test (15s)
✓ Tests executed

===== STEP 6: Check for Videos =====
✓ Video files found

===== STEP 7: Convert Videos to MP4 =====
Converting: Desktop video
✓ Converted: desktop-ui-test-20260123-120000.mp4 (2.1M)
Converting: Mobile video
✓ Converted: mobile-ui-test-20260123-120000.mp4 (1.4M)
✓ Converted 2 video(s)

===== STEP 8: Configure Git =====
✓ Git configured

===== STEP 9: Commit Videos =====
✓ Videos committed

===== STEP 10: Push to GitHub =====
✓ Pushed to GitHub

===== SUCCESS =====
Videos available at:
https://github.com/Adam-S-Daniel/scratch-claude-001/tree/claude/revamp-hamhock-ui-f9nXt/test-videos

✅ Success! Videos generated and pushed to GitHub
==================================================

View videos on GitHub:
  https://github.com/Adam-S-Daniel/scratch-claude-001/tree/claude/revamp-hamhock-ui-f9nXt/test-videos

Pull the latest changes locally:
  git pull origin claude/revamp-hamhock-ui-f9nXt
```

---

## Summary

**To generate videos right now:**

```bash
# One-time setup
export GITHUB_TOKEN='ghp_your_token'

# Run script
./sprite-generate-and-push.sh

# Wait 3-5 minutes
# Videos automatically pushed to GitHub!
```

**That's it!** Everything runs on the Sprite VM automatically. 🎉

---

## Additional Documentation

- **GITHUB_TOKEN_SETUP.md** - Detailed token setup guide
- **QUICK_START_VIDEO_PUSH.md** - Quick reference guide
- **playwright-ui-tests.js** - Test suite source code
