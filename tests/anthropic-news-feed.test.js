const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const NEWS_PATH = path.join(__dirname, '..', 'feed', 'anthropic-news.xml');

describe('Anthropic News Feed - File Existence', () => {
  it('should have the anthropic-news RSS feed file', () => {
    assert.ok(fs.existsSync(NEWS_PATH), 'feed/anthropic-news.xml should exist');
  });

  it('should not be empty', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.length > 0, 'RSS feed should not be empty');
  });
});

describe('Anthropic News Feed - XML Structure', () => {
  it('should start with XML declaration', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.startsWith('<?xml'), 'Should start with XML declaration');
    assert.ok(content.includes('encoding="UTF-8"'), 'Should specify UTF-8 encoding');
  });

  it('should have RSS 2.0 root element', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.includes('<rss version="2.0"'), 'Should have RSS 2.0 version');
    assert.ok(content.includes('</rss>'), 'Should close rss element');
  });

  it('should include Atom namespace', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(
      content.includes('xmlns:atom="http://www.w3.org/2005/Atom"'),
      'Should include Atom namespace'
    );
  });
});

describe('Anthropic News Feed - Channel Metadata', () => {
  it('should have title "Anthropic News"', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const titleMatch = content.match(/<channel>[\s\S]*?<title>(.+?)<\/title>/);
    assert.ok(titleMatch, 'Channel should have a title');
    assert.equal(titleMatch[1], 'Anthropic News');
  });

  it('should link to anthropic.com/news', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(
      content.includes('<link>https://www.anthropic.com/news</link>'),
      'Channel link should point to anthropic.com/news'
    );
  });

  it('should have a description', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const descMatch = content.match(/<channel>[\s\S]*?<description>(.+?)<\/description>/);
    assert.ok(descMatch, 'Channel should have a description');
    assert.ok(descMatch[1].length > 0, 'Description should not be empty');
  });

  it('should specify language as en-us', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.includes('<language>en-us</language>'), 'Should have en-us language');
  });

  it('should have atom:link self-reference', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.includes('atom:link') && content.includes('rel="self"'));
    assert.ok(content.includes('anthropic-news.xml'));
  });
});

describe('Anthropic News Feed - Items', () => {
  it('should contain at least 15 items', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const items = content.match(/<item>[\s\S]*?<\/item>/g);
    assert.ok(items, 'Should contain items');
    assert.ok(items.length >= 15, `Should have at least 15 items, found ${items.length}`);
  });

  it('every item should have a title', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      const title = item.match(/<title>(.+?)<\/title>/);
      assert.ok(title, 'Each item should have a title');
      assert.ok(title[1].length > 0, 'Item title should not be empty');
    }
  });

  it('every item should have a link to anthropic.com', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      const link = item.match(/<link>(.+?)<\/link>/);
      assert.ok(link, 'Each item should have a link');
      assert.ok(
        link[1].includes('anthropic.com/'),
        `Link should point to anthropic.com, got: ${link[1]}`
      );
    }
  });

  it('every item should have a guid and pubDate', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      assert.ok(item.match(/<guid[^>]*>.+?<\/guid>/), 'Each item should have a guid');
      const pubDate = item.match(/<pubDate>(.+?)<\/pubDate>/);
      assert.ok(pubDate, 'Each item should have a pubDate');
      assert.ok(!isNaN(new Date(pubDate[1]).getTime()), `Invalid date: ${pubDate[1]}`);
    }
  });

  it('every item should have a description', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      const desc = item.match(/<description>(.+?)<\/description>/);
      assert.ok(desc, 'Each item should have a description');
      assert.ok(desc[1].length > 20, 'Description should be meaningful');
    }
  });

  it('items should have unique guids', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const items = content.match(/<item>[\s\S]*?<\/item>/g);
    const guids = items.map(item => item.match(/<guid[^>]*>(.+?)<\/guid>/)[1]);
    assert.equal(new Set(guids).size, guids.length, 'All guids should be unique');
  });
});

describe('Anthropic News Feed - Known Posts', () => {
  it('should include Claude Opus 4.5 announcement', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.includes('anthropic.com/news/claude-opus-4-5'));
  });

  it('should include Claude Sonnet 4.5 announcement', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.includes('anthropic.com/news/claude-sonnet-4-5'));
  });

  it('should include the UK Government partnership', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.includes('anthropic.com/news/gov-UK-partnership'));
  });

  it('should include the Snowflake partnership', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    assert.ok(content.includes('anthropic.com/news/snowflake-anthropic-expanded-partnership'));
  });
});

describe('Anthropic News Feed - Valid XML', () => {
  it('should have balanced item tags', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const openItems = (content.match(/<item>/g) || []).length;
    const closeItems = (content.match(/<\/item>/g) || []).length;
    assert.equal(openItems, closeItems, 'Should have equal <item> and </item> tags');
  });

  it('should not contain unescaped ampersands', () => {
    const content = fs.readFileSync(NEWS_PATH, 'utf-8');
    const textBlocks = content.match(/>([^<]+)</g) || [];
    for (const block of textBlocks) {
      const text = block.slice(1, -1);
      const unescaped = text.match(/&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[\da-fA-F]+;)/g);
      assert.ok(!unescaped, `Unescaped ampersand in: "${text.substring(0, 50)}..."`);
    }
  });
});
