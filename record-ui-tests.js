#!/usr/bin/env node

/**
 * Ham Hock UI Test Recording using Sprites.dev + Playwright
 * This script creates a Sprite VM and runs Playwright browser tests with video recording
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

const SPRITES_API_KEY = 'adam-761/1425148/581fa386a123b3cee5e3ad6fddfd592c/9186abb5216275aea3799b4393266cb40c23188cdebb968a5292efbb13a9daf5';
const GAME_URL = 'https://adam-s-daniel.github.io/scratch-claude-001/ham-hock.html';
const SPRITE_NAME = `hamhock-test-${Date.now()}`;

console.log('🎬 Ham Hock UI Test Recording via Sprites.dev');
console.log('==============================================\n');

/**
 * Make API request to Sprites
 */
function makeSpritesRequest(method, path, data) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.sprites.dev',
            port: 443,
            path: path,
            method: method,
            headers: {
                'Authorization': `Bearer ${SPRITES_API_KEY}`,
                'Content-Type': 'application/json'
            }
        };

        const req = https.request(options, (res) => {
            let body = '';

            res.on('data', (chunk) => {
                body += chunk;
            });

            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    try {
                        resolve(body ? JSON.parse(body) : {});
                    } catch (e) {
                        resolve({ raw: body });
                    }
                } else {
                    reject(new Error(`HTTP ${res.statusCode}: ${body}`));
                }
            });
        });

        req.on('error', reject);

        if (data) {
            req.write(JSON.stringify(data));
        }

        req.end();
    });
}

/**
 * Create a Sprite VM
 */
async function createSprite() {
    console.log(`📦 Creating Sprite VM: ${SPRITE_NAME}...`);

    try {
        await makeSpritesRequest('PUT', `/v1/sprites/${SPRITE_NAME}`, {});
        console.log('✓ Sprite VM created\n');
        return SPRITE_NAME;
    } catch (error) {
        console.error('✗ Failed to create Sprite:', error.message);
        throw error;
    }
}

/**
 * Execute command in Sprite
 */
async function execInSprite(spriteName, command, description) {
    console.log(`⚙️  ${description}...`);

    try {
        const result = await makeSpritesRequest('POST', `/v1/sprites/${spriteName}/exec`, {
            command: ['/bin/bash', '-c', command],
            timeout: 300000 // 5 minutes
        });

        if (result.stdout) {
            console.log(result.stdout);
        }
        if (result.stderr) {
            console.error('stderr:', result.stderr);
        }

        console.log(`✓ ${description} completed\n`);
        return result;
    } catch (error) {
        console.error(`✗ ${description} failed:`, error.message);
        throw error;
    }
}

/**
 * Setup Playwright in Sprite
 */
async function setupPlaywright(spriteName) {
    // Install Node.js and Playwright
    await execInSprite(spriteName,
        'curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs',
        'Installing Node.js'
    );

    await execInSprite(spriteName,
        'npm install -g playwright@latest && npx playwright install --with-deps chromium',
        'Installing Playwright and Chrome'
    );
}

/**
 * Create and upload test script
 */
async function uploadTestScript(spriteName) {
    const testScript = `
const { chromium } = require('playwright');

(async () => {
    console.log('🎬 Starting Ham Hock UI Tests...\\\\n');

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    // Desktop test
    console.log('📹 Recording Desktop Tests...\\n');
    const desktopContext = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        recordVideo: {
            dir: '/tmp/videos',
            size: { width: 1920, height: 1080 }
        }
    });

    const desktopPage = await desktopContext.newPage();
    await desktopPage.goto('${GAME_URL}', { waitUntil: 'networkidle' });

    // Wait for Three.js to load
    await desktopPage.waitForFunction(() => typeof THREE !== 'undefined', { timeout: 10000 });
    console.log('✓ Three.js loaded');

    // Wait for 3D rendering to initialize
    await desktopPage.waitForTimeout(3000);

    // Start game
    await desktopPage.click('button.primary-btn:has-text("BEGIN MY DESTINY")');
    console.log('✓ Clicked BEGIN MY DESTINY');
    await desktopPage.waitForTimeout(3000);

    // Test size selection
    console.log('\\nTesting size selection...');
    const sizeButtons = await desktopPage.$$('#sizeOptions .option-btn:not(.locked)');
    for (let i = 0; i < Math.min(3, sizeButtons.length); i++) {
        const text = await sizeButtons[i].textContent();
        await sizeButtons[i].click();
        console.log(\`✓ Selected size: \${text.trim()}\`);
        await desktopPage.waitForTimeout(2000);
    }

    // Test color selection
    console.log('\\nTesting color selection...');
    const colorButtons = await desktopPage.$$('#colorOptions .option-btn:not(.locked)');
    for (let i = 0; i < Math.min(4, colorButtons.length); i++) {
        const text = await colorButtons[i].textContent();
        await colorButtons[i].click();
        console.log(\`✓ Selected color: \${text.trim()}\`);
        await desktopPage.waitForTimeout(2000);
    }

    // Test BOW TIE (critical!)
    console.log('\\n🎀 Testing BOW TIE accessory (CRITICAL)...');
    const accessoryButtons = await desktopPage.$$('#accessoryOptions .option-btn');
    for (const btn of accessoryButtons) {
        const text = await btn.textContent();
        if (text.includes('Bow Tie') && !(await btn.getAttribute('class')).includes('locked')) {
            await btn.click();
            console.log('✓ BOW TIE SELECTED - Should be HUGE and visible!');
            await desktopPage.waitForTimeout(4000);

            // Verify in game state
            const isBowTie = await desktopPage.evaluate(() => {
                return gameState?.currentHock?.accessory === 'Bow Tie';
            });
            console.log(\`✓ Bow tie state: \${isBowTie ? 'CONFIRMED' : 'Not set'}\`);
            break;
        }
    }

    // Test other accessories
    console.log('\\nTesting other accessories...');
    for (let i = 0; i < Math.min(3, accessoryButtons.length); i++) {
        const text = await accessoryButtons[i].textContent();
        if (!(await accessoryButtons[i].getAttribute('class')).includes('locked')) {
            await accessoryButtons[i].click();
            console.log(\`✓ Selected: \${text.trim()}\`);
            await desktopPage.waitForTimeout(2000);
        }
    }

    // Back to bow tie
    for (const btn of accessoryButtons) {
        const text = await btn.textContent();
        if (text.includes('Bow Tie')) {
            await btn.click();
            console.log('\\n✓ Bow tie selected again for final showcase');
            await desktopPage.waitForTimeout(3000);
            break;
        }
    }

    // Submit to judges
    console.log('\\nSubmitting to judges...');
    await desktopPage.click('button.primary-btn:has-text("PRESENT TO JUDGES")');
    await desktopPage.waitForTimeout(6000);
    console.log('✓ Judging phase rendered');

    await desktopPage.waitForTimeout(3000);
    await desktopContext.close();

    // Mobile test
    console.log('\\n📱 Recording Mobile Tests...\\n');
    const mobileContext = await browser.newContext({
        viewport: { width: 375, height: 667 },
        isMobile: true,
        hasTouch: true,
        recordVideo: {
            dir: '/tmp/videos',
            size: { width: 375, height: 667 }
        }
    });

    const mobilePage = await mobileContext.newPage();
    await mobilePage.goto('${GAME_URL}', { waitUntil: 'networkidle' });
    await mobilePage.waitForFunction(() => typeof THREE !== 'undefined');
    await mobilePage.waitForTimeout(3000);

    // Start game on mobile
    await mobilePage.click('button.primary-btn');
    console.log('✓ Started game on mobile');
    await mobilePage.waitForTimeout(3000);

    // Verify mobile layout
    const layout = await mobilePage.evaluate(() => {
        const hock = document.querySelector('.hock-display');
        const options = document.querySelector('.options-panel');
        return {
            hockHeight: hock?.offsetHeight,
            hockVisible: hock?.offsetHeight > 0,
            optionsHeight: options?.offsetHeight,
            optionsScrollable: options?.scrollHeight > options?.offsetHeight
        };
    });
    console.log('✓ Mobile layout:', JSON.stringify(layout, null, 2));

    // Test bow tie on mobile
    const mobileBowTieBtn = await mobilePage.$('#accessoryOptions .option-btn:has-text("Bow Tie")');
    if (mobileBowTieBtn) {
        await mobileBowTieBtn.click();
        console.log('✓ BOW TIE selected on mobile');
        await mobilePage.waitForTimeout(3000);
    }

    // Test scrolling
    await mobilePage.evaluate(() => {
        document.querySelector('.options-panel')?.scrollBy(0, 200);
    });
    console.log('✓ Tested mobile scrolling');
    await mobilePage.waitForTimeout(2000);

    // Change some options on mobile
    await mobilePage.click('#sizeOptions .option-btn:not(.locked)');
    await mobilePage.waitForTimeout(2000);
    await mobilePage.click('#colorOptions .option-btn:not(.locked)');
    await mobilePage.waitForTimeout(2000);

    await mobileContext.close();
    await browser.close();

    console.log('\\n✅ All tests completed!');
    console.log('Videos saved to /tmp/videos/');
})();
`;

    console.log('📝 Uploading test script...');

    // Write test script to Sprite
    await execInSprite(spriteName,
        `cat > /tmp/test-hamhock.js << 'ENDOFSCRIPT'\n${testScript}\nENDOFSCRIPT`,
        'Creating test script'
    );

    await execInSprite(spriteName,
        'cd /tmp && npm install playwright',
        'Installing Playwright in test directory'
    );
}

/**
 * Run tests and get videos
 */
async function runTests(spriteName) {
    console.log('🎬 Running UI tests with video recording...\n');

    await execInSprite(spriteName,
        'mkdir -p /tmp/videos && cd /tmp && node test-hamhock.js',
        'Executing Playwright tests'
    );

    // List video files
    const result = await execInSprite(spriteName,
        'ls -lh /tmp/videos/',
        'Listing recorded videos'
    );

    return result;
}

/**
 * Download video from Sprite
 */
async function downloadVideos(spriteName) {
    console.log('⬇️  Downloading videos from Sprite...\n');

    // Get list of video files
    const listResult = await execInSprite(spriteName,
        'ls /tmp/videos/*.webm 2>/dev/null || echo "No videos found"',
        'Finding video files'
    );

    if (!listResult.stdout || listResult.stdout.includes('No videos found')) {
        console.log('⚠️  No video files found');
        return;
    }

    const videoFiles = listResult.stdout.trim().split('\n');
    console.log(`Found ${videoFiles.length} video(s)`);

    // Note: Sprites.dev doesn't have a direct file download API
    // Videos would need to be accessed via the Sprite's HTTP interface
    // or by setting up a file server within the Sprite

    console.log('\n📹 Videos recorded in Sprite VM at:', videoFiles.join(', '));
    console.log('\n💡 To download videos, you can:');
    console.log(`   1. Access Sprite console: sprite console ${spriteName}`);
    console.log('   2. Set up HTTP server in Sprite to download files');
    console.log('   3. Use sprite exec to copy files to accessible location');
}

/**
 * Cleanup
 */
async function cleanup(spriteName) {
    console.log(`\n🧹 Cleaning up Sprite: ${spriteName}...`);

    try {
        await makeSpritesRequest('DELETE', `/v1/sprites/${spriteName}`, null);
        console.log('✓ Sprite deleted');
    } catch (error) {
        console.error('⚠️  Cleanup failed:', error.message);
    }
}

/**
 * Main execution
 */
async function main() {
    let spriteName = null;

    try {
        // Create Sprite
        spriteName = await createSprite();

        // Setup environment
        await setupPlaywright(spriteName);

        // Upload test script
        await uploadTestScript(spriteName);

        // Run tests
        await runTests(spriteName);

        // Get videos
        await downloadVideos(spriteName);

        console.log('\n✅ Test recording completed successfully!');
        console.log('===========================================');
        console.log(`\nSprite Name: ${spriteName}`);
        console.log('Videos Location: /tmp/videos/ in Sprite VM');
        console.log('\nTo access videos:');
        console.log(`  sprite console ${spriteName}`);
        console.log('  cd /tmp/videos && ls -lh');

    } catch (error) {
        console.error('\\n❌ Error:', error.message);
        console.error(error.stack);
        process.exit(1);
    } finally {
        // Optionally cleanup (comment out to keep Sprite for manual access)
        // if (spriteName) {
        //     await cleanup(spriteName);
        // }
    }
}

// Run
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { createSprite, setupPlaywright, uploadTestScript, runTests };
