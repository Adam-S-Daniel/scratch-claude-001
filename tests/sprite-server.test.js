const { describe, it, before, after } = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { spawn } = require('node:child_process');
const path = require('node:path');

const SERVER_PATH = path.join(__dirname, '..', 'sprite', 'server.js');
const PORT = 9876; // Use a non-default port to avoid conflicts

function get(urlPath) {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:${PORT}${urlPath}`, (res) => {
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body }));
    }).on('error', reject);
  });
}

describe('Sprite Server', () => {
  let server;

  before(async () => {
    // Start the server on a test port
    server = spawn(process.execPath, [SERVER_PATH], {
      env: { ...process.env, PORT: String(PORT) },
      stdio: 'pipe',
    });
    // Wait for the server to be ready
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('Server did not start')), 5000);
      server.stdout.on('data', (data) => {
        if (data.toString().includes('listening')) {
          clearTimeout(timeout);
          resolve();
        }
      });
      server.on('error', reject);
    });
  });

  after(() => {
    if (server) server.kill();
  });

  it('should serve the index page at /', async () => {
    const res = await get('/');
    assert.equal(res.status, 200);
    assert.ok(res.headers['content-type'].includes('text/html'));
    assert.ok(res.body.includes('announcements.xml'));
    assert.ok(res.body.includes('anthropic-news.xml'));
  });

  it('should return 404 for unknown paths', async () => {
    const res = await get('/nonexistent');
    assert.equal(res.status, 404);
  });

  describe('Announcements feed endpoint', () => {
    it('should serve valid RSS at /feed/announcements.xml', async () => {
      const res = await get('/feed/announcements.xml');
      assert.equal(res.status, 200);
      assert.ok(res.headers['content-type'].includes('application/rss+xml'));
      assert.ok(res.body.startsWith('<?xml'));
      assert.ok(res.body.includes('<rss version="2.0"'));
    });

    it('should have Cache-Control header with max-age=60', async () => {
      const res = await get('/feed/announcements.xml');
      assert.ok(res.headers['cache-control'].includes('max-age=60'));
    });

    it('should contain Claude announcement items', async () => {
      const res = await get('/feed/announcements.xml');
      assert.ok(res.body.includes('claude.com/blog/'));
      assert.ok(res.body.includes('<item>'));
      const items = res.body.match(/<item>/g);
      assert.ok(items.length >= 10, `Expected >=10 items, got ${items.length}`);
    });

    it('should link to announcements category page', async () => {
      const res = await get('/feed/announcements.xml');
      assert.ok(res.body.includes('<link>https://claude.com/blog/category/announcements</link>'));
    });

    it('should use server-side caching (1-min debounce)', async () => {
      // Two rapid requests should return identical lastBuildDate (same cached response)
      const res1 = await get('/feed/announcements.xml');
      const res2 = await get('/feed/announcements.xml');
      const date1 = res1.body.match(/<lastBuildDate>(.+?)<\/lastBuildDate>/)[1];
      const date2 = res2.body.match(/<lastBuildDate>(.+?)<\/lastBuildDate>/)[1];
      assert.equal(date1, date2, 'Cached responses should have identical lastBuildDate');
    });
  });

  describe('Anthropic News feed endpoint', () => {
    it('should serve valid RSS at /feed/anthropic-news.xml', async () => {
      const res = await get('/feed/anthropic-news.xml');
      assert.equal(res.status, 200);
      assert.ok(res.headers['content-type'].includes('application/rss+xml'));
      assert.ok(res.body.startsWith('<?xml'));
      assert.ok(res.body.includes('<rss version="2.0"'));
    });

    it('should have Cache-Control header with max-age=60', async () => {
      const res = await get('/feed/anthropic-news.xml');
      assert.ok(res.headers['cache-control'].includes('max-age=60'));
    });

    it('should contain Anthropic news items', async () => {
      const res = await get('/feed/anthropic-news.xml');
      assert.ok(res.body.includes('anthropic.com/'));
      assert.ok(res.body.includes('<item>'));
      const items = res.body.match(/<item>/g);
      assert.ok(items.length >= 15, `Expected >=15 items, got ${items.length}`);
    });

    it('should link to anthropic.com/news', async () => {
      const res = await get('/feed/anthropic-news.xml');
      assert.ok(res.body.includes('<link>https://www.anthropic.com/news</link>'));
    });

    it('should use server-side caching (1-min debounce)', async () => {
      const res1 = await get('/feed/anthropic-news.xml');
      const res2 = await get('/feed/anthropic-news.xml');
      const date1 = res1.body.match(/<lastBuildDate>(.+?)<\/lastBuildDate>/)[1];
      const date2 = res2.body.match(/<lastBuildDate>(.+?)<\/lastBuildDate>/)[1];
      assert.equal(date1, date2, 'Cached responses should have identical lastBuildDate');
    });
  });
});
