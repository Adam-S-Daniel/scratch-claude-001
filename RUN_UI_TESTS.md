# Running Ham Hock UI Tests - Complete Guide

## ✅ What's Been Completed

All test infrastructure is now committed and pushed to the repository:

1. **Playwright Test Suite** (`playwright-ui-tests.js`)
   - Desktop tests with full game flow
   - Mobile responsive layout tests
   - BOW TIE accessory verification
   - Video recording enabled

2. **Configuration Files**
   - `playwright.config.js` - Test configuration
   - `package.json` - Dependencies and scripts
   - `.gitignore` - Excludes test results from repo

3. **Documentation**
   - `UI_TEST_VIDEO_GUIDE.md` - Comprehensive testing guide
   - `UI_TEST_DOCUMENTATION.md` - Test scenarios and requirements

4. **Sprites.dev Integration** (Ready to use)
   - CLI installed at `/root/.local/bin/sprite`
   - Scripts ready: `record-ui-tests.js`, `test-ui-recording.js`

---

## 🚀 Quick Start - Run Tests Locally

### Option 1: Using Playwright (Recommended for immediate results)

```bash
# Install dependencies
npm install

# Install Playwright browser
npx playwright install chromium

# Run tests with video recording
npm run test

# View results
npx playwright show-report test-results/html-report
```

### Option 2: Run with visible browser (see tests in action)

```bash
npm run test:headed
```

### Option 3: Debug mode

```bash
npm run test:debug
```

---

## 🎥 Video Outputs

After running tests, you'll find:

**Videos:**
- `test-results/videos/` - WebM format recordings
  - Desktop test (~35 seconds)
  - Mobile test (~15 seconds)

**Screenshots:**
- `screenshots/01-landing.png`
- `screenshots/05-BOWTIE-HUGE.png` - **BOW TIE showcase**
- `screenshots/mobile-*.png`

**HTML Report:**
- `test-results/html-report/index.html` - Interactive report with videos

---

## ☁️ Using Sprites.dev CLI (Cloud Testing)

### Prerequisites

Sprites CLI is already installed. You need to authenticate:

```bash
export PATH="/root/.local/bin:$PATH"
sprite login
```

### Create and Use Sprite

```bash
# Create a Sprite VM
sprite create hamhock-test-ui

# Open interactive console
sprite console hamhock-test-ui
```

### Inside the Sprite, run:

```bash
# Install dependencies
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs git

# Clone repo
git clone https://github.com/Adam-S-Daniel/scratch-claude-001.git
cd scratch-claude-001
git checkout claude/revamp-hamhock-ui-f9nXt

# Run tests
npm install
npx playwright install --with-deps chromium
npm run test

# Videos will be in test-results/videos/
ls -lh test-results/videos/
```

### Download Videos from Sprite

```bash
# On your local machine
sprite exec hamhock-test-ui "cd scratch-claude-001 && tar czf /tmp/videos.tar.gz test-results/videos/"

# Then access via HTTP or copy using sprite console
```

---

## 📋 Test Coverage

The automated tests verify:

### Desktop Tests (1920x1080)
- ✅ Three.js initialization
- ✅ 3D rendering with photo-realistic materials
- ✅ Continuous rotation animation
- ✅ Size selection (Dainty, Regular)
- ✅ Color selection (Natural Pink, Hickory Smoked)
- ✅ **BOW TIE accessory (HUGE, 2x scale, 3D)**
- ✅ Other accessories (Top Hat, Monocle, etc.)
- ✅ Seasoning selection
- ✅ Complete game flow (design → judging)
- ✅ Judging phase 3D rendering

### Mobile Tests (375x667)
- ✅ Mobile split-screen layout
- ✅ Ham hock visible at top (35vh)
- ✅ Options scrollable below
- ✅ BOW TIE rendering on mobile
- ✅ Scroll behavior (ham hock stays visible)
- ✅ Touch interactions

---

## 🎯 Critical Test: BOW TIE

The BOW TIE test specifically verifies:

1. **Selection:** Clicking "Bow Tie" updates game state
2. **3D Rendering:** Bow tie geometry added to scene (line 812: `hockGroup.add(bowTie)`)
3. **HUGE Scale:** Bow tie scaled 2x (line 657: `bowTieGroup.scale.set(2, 2, 2)`)
4. **Visibility:** Bow tie visible in both design and judging phases
5. **Mobile:** Bow tie renders correctly on small screens

Test assertion at `playwright-ui-tests.js:85`:
```javascript
expect(accessory).toBe('Bow Tie');
expect(bowTieRendered).toBe(true);
```

---

## 📊 Test Results

Expected output:

```
✓ Desktop UI - Full Game Flow with 3D Rendering (35s)
  ✓ Page loaded
  ✓ Three.js loaded
  ✓ 3D viewers initialized
  ✓ Selected size: Dainty
  ✓ Selected size: Regular
  ✓ Selected color: Natural Pink
  ✓ Selected color: Hickory Smoked
  ✓ BOW TIE CLICKED
  ✓ BOW TIE STATE CONFIRMED
  ✓ BOW TIE RENDERED IN 3D SCENE

✓ Mobile UI - Responsive Layout Test (15s)
  ✓ Started game on mobile
  ✓ Mobile split-screen layout confirmed
  ✓ BOW TIE selected on mobile
  ✓ Ham hock still visible with bow tie
  ✓ Ham hock stays visible during scroll

2 passed (50s)
```

---

## 🛠️ Troubleshooting

### Issue: Playwright not installed
```bash
npx playwright install --with-deps chromium
```

### Issue: Tests fail to start
```bash
# Check if GitHub Pages is accessible
curl -I https://adam-s-daniel.github.io/scratch-claude-001/ham-hock.html

# Should return 200 OK
```

### Issue: Videos not generated
Edit `playwright.config.js` and ensure:
```javascript
use: {
  video: 'on',  // Must be 'on'
}
```

### Issue: Sprites authentication
```bash
# Interactive login
sprite login

# Or set API token
export FLY_API_TOKEN="your-token-here"
```

---

## 📦 Files Reference

| File | Purpose |
|------|---------|
| `playwright-ui-tests.js` | Main test suite with video recording |
| `playwright.config.js` | Playwright configuration |
| `package.json` | Dependencies and npm scripts |
| `UI_TEST_VIDEO_GUIDE.md` | Comprehensive testing documentation |
| `record-ui-tests.js` | Sprites.dev API automation |
| `.gitignore` | Excludes test results from git |

---

## 🎬 Next Steps

1. **Run tests locally:**
   ```bash
   npm install && npx playwright install chromium && npm run test
   ```

2. **View results:**
   ```bash
   npx playwright show-report test-results/html-report
   ```

3. **Convert videos to MP4:**
   ```bash
   ffmpeg -i test-results/videos/*.webm -c:v libx264 hamhock-ui-tests.mp4
   ```

4. **Upload to GitHub:**
   - Videos can be added to GitHub Releases
   - Or upload to cloud storage (Drive, YouTube, Loom)

---

## 📚 Resources

- **Playwright Docs:** https://playwright.dev/docs/videos
- **Sprites.dev Docs:** https://docs.sprites.dev/cli/commands/
- **Game URL:** https://adam-s-daniel.github.io/scratch-claude-001/ham-hock.html
- **Repository:** https://github.com/Adam-S-Daniel/scratch-claude-001

---

## ✨ Summary

All UI test infrastructure is **committed and ready**. The tests comprehensively validate:

- ✅ 3D rendering with Three.js
- ✅ Photo-realistic materials and lighting
- ✅ **HUGE bow tie accessory (2x scale)**
- ✅ Mobile responsive split-screen layout
- ✅ Complete game flow

**To generate test videos now:**
```bash
npm install && npx playwright install chromium && npm run test
```

Videos will be saved in `test-results/videos/` with full coverage of all features including the HUGE bow tie!

---

**Sources:**
- [Sprites.dev CLI Commands](https://docs.sprites.dev/cli/commands/)
- [Sprites Installation](https://simonwillison.net/2026/Jan/9/sprites-dev/)
- [Sprites API](https://sprites.dev/api/sprites)
