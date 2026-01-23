# Ham Hock UI Test Video Recording Guide

This guide provides multiple methods to record comprehensive UI test videos for the Ham Hock Design Quest 3D game.

## Quick Start (Recommended)

### Method 1: Local Playwright (Easiest)

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install chromium

# Run tests with video recording
npm run test

# Or run with visible browser
npm run test:headed

# View HTML report with videos
npx playwright show-report test-results/html-report
```

Videos will be saved in: `test-results/`
Screenshots will be saved in: `screenshots/`

---

## Method 2: Using Sprites.dev (Cloud Execution)

Sprites.dev provides isolated cloud VMs for running browser automation. Here's how to use it:

### Prerequisites
- Sprites API Key: `adam-761/1425148/581fa386a123b3cee5e3ad6fddfd592c/9186abb5216275aea3799b4393266cb40c23188cdebb968a5292efbb13a9daf5`
- Install Sprites CLI: `npm install -g @fly/sprites-cli`

### Option A: Using Sprites CLI

```bash
# Create a Sprite VM
sprite create hamhock-test

# Open console
sprite console hamhock-test

# Inside the Sprite, run:
apt-get update && apt-get install -y curl git
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Clone or copy test files
git clone https://github.com/Adam-S-Daniel/scratch-claude-001.git
cd scratch-claude-001

# Install dependencies
npm install
npx playwright install --with-deps chromium

# Run tests
npm run test

# Videos are saved in test-results/
# To download, you can use sprite's HTTP interface or set up a simple server
```

### Option B: Using Sprites API (Automated)

The `record-ui-tests.js` script automates this process:

```bash
node record-ui-tests.js
```

This will:
1. Create a Sprite VM
2. Install Node.js and Playwright
3. Upload and run the test script
4. Record videos
5. Videos will be accessible in the Sprite VM at `/tmp/videos/`

To access the videos:
```bash
sprite console hamhock-test-<timestamp>
cd /tmp/videos
ls -lh
```

---

## Method 3: Manual Screen Recording

If automated solutions don't work, you can manually record:

### Using OBS Studio (Free, Cross-platform)

1. Download OBS Studio: https://obsproject.com/
2. Add Browser Source:
   - URL: https://adam-s-daniel.github.io/scratch-claude-001/ham-hock.html
   - Width: 1920, Height: 1080
3. Start Recording
4. Follow the test steps below
5. Stop Recording

### Using Browser DevTools

Many browsers have built-in video recording:

#### Chrome DevTools Recorder
1. Open DevTools (F12)
2. Go to "Recorder" panel
3. Click "Create a new recording"
4. Perform test actions
5. Export as video

---

## Test Script Walkthrough

The automated tests cover:

### Desktop Tests (1920x1080)
1. **Page Load & 3D Initialization** (3s)
   - Verify Three.js loads
   - Wait for 3D rendering

2. **Start Game** (3s)
   - Click "BEGIN MY DESTINY"
   - Verify design phase loads

3. **Size Selection** (5s)
   - Test Dainty size
   - Test Regular size
   - Verify 3D model scales

4. **Color Selection** (5s)
   - Test Natural Pink
   - Test Hickory Smoked
   - Verify material updates

5. **BOW TIE Test** (4s) ⭐ CRITICAL
   - Select Bow Tie accessory
   - Verify HUGE bow tie renders
   - Confirm 3D geometry added

6. **Other Accessories** (4s)
   - Test additional accessories
   - Return to bow tie

7. **Seasoning Selection** (3s)
   - Test Classic Salt & Pepper
   - Test Cajun Spice

8. **Submit to Judges** (8s)
   - Present ham hock
   - Verify judging phase 3D render

**Total Desktop Test Duration: ~35 seconds**

### Mobile Tests (375x667)
1. **Page Load** (3s)
2. **Start Game** (3s)
3. **Verify Split-Screen Layout** (0s)
   - Confirm ham hock visible at top
   - Confirm options scrollable below
4. **Select Bow Tie on Mobile** (3s)
5. **Test Scrolling** (2s)
   - Scroll options panel
   - Verify ham hock stays visible
6. **Change Options** (4s)

**Total Mobile Test Duration: ~15 seconds**

---

## Video Artifacts Generated

### Desktop Recording
- **Filename**: `test-results/videos/chromium-desktop-*.webm`
- **Duration**: ~35 seconds
- **Resolution**: 1920x1080
- **Shows**:
  - Full 3D rendering
  - All option selections
  - HUGE bow tie accessory
  - Complete game flow

### Mobile Recording
- **Filename**: `test-results/videos/chromium-mobile-*.webm`
- **Duration**: ~15 seconds
- **Resolution**: 375x667
- **Shows**:
  - Mobile split-screen layout
  - Ham hock + options both visible
  - Touch interactions
  - Scroll behavior

### Screenshots
- `screenshots/01-landing.png` - Initial page
- `screenshots/02-game-start.png` - Design phase
- `screenshots/03-after-sizes.png` - After size selection
- `screenshots/04-after-colors.png` - After color selection
- `screenshots/05-BOWTIE-HUGE.png` - **BOW TIE showcase**
- `screenshots/06-bowtie-final.png` - Final bow tie view
- `screenshots/07-judging-phase.png` - Judging phase
- `screenshots/mobile-*.png` - Mobile views

---

## Converting Videos

Playwright records in WebM format. To convert to MP4:

```bash
# Using ffmpeg
ffmpeg -i test-results/videos/*.webm -c:v libx264 -c:a aac hamhock-desktop-tests.mp4

# Batch convert all
for file in test-results/videos/*.webm; do
    ffmpeg -i "$file" -c:v libx264 -c:a aac "${file%.webm}.mp4"
done
```

---

## Troubleshooting

### Issue: Tests fail to run
**Solution**: Ensure Playwright browsers are installed:
```bash
npx playwright install --with-deps chromium
```

### Issue: No videos generated
**Solution**: Check video configuration in `playwright.config.js`:
```javascript
use: {
  video: 'on',  // Make sure this is 'on'
}
```

### Issue: 3D rendering not working in tests
**Solution**: Playwright needs hardware acceleration. Add to config:
```javascript
use: {
  launchOptions: {
    args: ['--use-gl=egl']
  }
}
```

### Issue: Sprites.dev API connection fails
**Solution**:
1. Check API key is correct
2. Verify network connectivity
3. Try using Sprites CLI instead of API

---

## Test Success Criteria

All tests should pass with these confirmations:

- ✅ Three.js loads successfully
- ✅ 3D ham hock renders and rotates
- ✅ All size selections work and update 3D model
- ✅ All color selections work and update materials
- ✅ **BOW TIE accessory renders HUGE and in 3D**
- ✅ Other accessories render correctly
- ✅ Judging phase shows 3D ham hock
- ✅ Mobile layout: ham hock and options both visible
- ✅ Mobile scrolling works correctly
- ✅ No console errors

---

## Video Upload Locations

Once recorded, videos can be:

1. **Committed to repo** (if small enough):
   ```bash
   git add test-results/videos/*.mp4
   git commit -m "Add UI test videos"
   ```

2. **Uploaded to cloud storage**:
   - GitHub Releases
   - Google Drive
   - YouTube (as unlisted)
   - Loom

3. **Added as artifact** in CI/CD:
   - GitHub Actions artifacts
   - CircleCI artifacts

---

## Files Reference

- **playwright-ui-tests.js** - Main test file
- **playwright.config.js** - Playwright configuration
- **package.json** - Dependencies and scripts
- **record-ui-tests.js** - Sprites.dev automation script
- **test-ui-recording.js** - Alternative recording script

---

## Need Help?

- Playwright Docs: https://playwright.dev/docs/videos
- Sprites.dev Docs: https://sprites.dev/api/sprites
- Ham Hock Game: https://adam-s-daniel.github.io/scratch-claude-001/ham-hock.html

---

## Summary

**Recommended Approach**: Use Method 1 (Local Playwright)

```bash
npm install
npx playwright install chromium
npm run test
```

Videos will be in `test-results/` and can be viewed in the HTML report:
```bash
npx playwright show-report test-results/html-report
```

This generates professional test videos with:
- ✅ Desktop and mobile views
- ✅ Full coverage of all features
- ✅ BOW TIE showcase
- ✅ Automated test assertions
- ✅ Screenshots at key moments
