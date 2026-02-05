const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const RSS_PATH = path.join(__dirname, '..', 'feed', 'announcements.xml');

describe('RSS Feed - File Existence', () => {
  it('should have the announcements RSS feed file', () => {
    assert.ok(fs.existsSync(RSS_PATH), 'feed/announcements.xml should exist');
  });

  it('should not be empty', () => {
    const content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.length > 0, 'RSS feed should not be empty');
  });
});

describe('RSS Feed - XML Structure', () => {
  let content;

  it('should start with XML declaration', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.startsWith('<?xml'), 'Should start with XML declaration');
    assert.ok(content.includes('encoding="UTF-8"'), 'Should specify UTF-8 encoding');
  });

  it('should have RSS 2.0 root element', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('<rss version="2.0"'), 'Should have RSS 2.0 version');
    assert.ok(content.includes('</rss>'), 'Should close rss element');
  });

  it('should include Atom namespace for self-referencing link', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(
      content.includes('xmlns:atom="http://www.w3.org/2005/Atom"'),
      'Should include Atom namespace'
    );
  });

  it('should have a channel element', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('<channel>'), 'Should have opening channel tag');
    assert.ok(content.includes('</channel>'), 'Should have closing channel tag');
  });
});

describe('RSS Feed - Channel Metadata', () => {
  let content;

  it('should have a channel title', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    const titleMatch = content.match(/<channel>[\s\S]*?<title>(.+?)<\/title>/);
    assert.ok(titleMatch, 'Channel should have a title');
    assert.ok(titleMatch[1].length > 0, 'Title should not be empty');
  });

  it('should link to the announcements category page', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(
      content.includes('<link>https://claude.com/blog/category/announcements</link>'),
      'Channel link should point to the announcements category'
    );
  });

  it('should have a channel description', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    const descMatch = content.match(/<channel>[\s\S]*?<description>(.+?)<\/description>/);
    assert.ok(descMatch, 'Channel should have a description');
    assert.ok(descMatch[1].length > 0, 'Description should not be empty');
  });

  it('should specify language as en-us', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('<language>en-us</language>'), 'Should have en-us language');
  });

  it('should have a lastBuildDate', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('<lastBuildDate>'), 'Should have lastBuildDate');
  });

  it('should have an atom:link self-reference', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(
      content.includes('atom:link') && content.includes('rel="self"'),
      'Should have atom:link self-reference'
    );
    assert.ok(
      content.includes('type="application/rss+xml"'),
      'Self-reference should have RSS content type'
    );
  });
});

describe('RSS Feed - Items', () => {
  let content;
  let items;

  it('should contain multiple items', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    items = content.match(/<item>[\s\S]*?<\/item>/g);
    assert.ok(items, 'Should contain items');
    assert.ok(items.length >= 10, `Should have at least 10 items, found ${items.length}`);
  });

  it('every item should have a title', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      const title = item.match(/<title>(.+?)<\/title>/);
      assert.ok(title, 'Each item should have a title');
      assert.ok(title[1].length > 0, 'Item title should not be empty');
    }
  });

  it('every item should have a link to claude.com/blog', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      const link = item.match(/<link>(.+?)<\/link>/);
      assert.ok(link, 'Each item should have a link');
      assert.ok(
        link[1].startsWith('https://claude.com/blog/'),
        `Link should point to claude.com/blog, got: ${link[1]}`
      );
    }
  });

  it('every item should have a guid', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      const guid = item.match(/<guid[^>]*>(.+?)<\/guid>/);
      assert.ok(guid, 'Each item should have a guid');
    }
  });

  it('every item should have a pubDate', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      const pubDate = item.match(/<pubDate>(.+?)<\/pubDate>/);
      assert.ok(pubDate, 'Each item should have a pubDate');
      // Verify it's a valid RFC 2822 date
      const date = new Date(pubDate[1]);
      assert.ok(!isNaN(date.getTime()), `pubDate should be a valid date: ${pubDate[1]}`);
    }
  });

  it('every item should have a description', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    items = content.match(/<item>[\s\S]*?<\/item>/g);
    for (const item of items) {
      const desc = item.match(/<description>(.+?)<\/description>/);
      assert.ok(desc, 'Each item should have a description');
      assert.ok(desc[1].length > 20, 'Description should be meaningful (>20 chars)');
    }
  });

  it('items should have unique guids', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    items = content.match(/<item>[\s\S]*?<\/item>/g);
    const guids = items.map(item => {
      const match = item.match(/<guid[^>]*>(.+?)<\/guid>/);
      return match[1];
    });
    const uniqueGuids = new Set(guids);
    assert.equal(uniqueGuids.size, guids.length, 'All guids should be unique');
  });

  it('items should be ordered by date (newest first)', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    items = content.match(/<item>[\s\S]*?<\/item>/g);
    const dates = items.map(item => {
      const match = item.match(/<pubDate>(.+?)<\/pubDate>/);
      return new Date(match[1]);
    });
    for (let i = 1; i < dates.length; i++) {
      assert.ok(
        dates[i] <= dates[i - 1],
        `Items should be in reverse chronological order: ${dates[i - 1].toISOString()} should be >= ${dates[i].toISOString()}`
      );
    }
  });
});

describe('RSS Feed - Known Announcements', () => {
  let content;

  it('should include the Cowork announcement', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('claude.com/blog/cowork-research-preview'), 'Should include Cowork post');
  });

  it('should include the Claude Code on the web announcement', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('claude.com/blog/claude-code-on-the-web'), 'Should include Claude Code on the web post');
  });

  it('should include the Max Plan announcement', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('claude.com/blog/max-plan'), 'Should include Max Plan post');
  });

  it('should include the Integrations announcement', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('claude.com/blog/integrations'), 'Should include Integrations post');
  });

  it('should include the Microsoft 365 Copilot announcement', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(
      content.includes('claude.com/blog/claude-now-available-in-microsoft-365-copilot'),
      'Should include Microsoft 365 Copilot post'
    );
  });

  it('should include the Agent Skills announcement', () => {
    content = fs.readFileSync(RSS_PATH, 'utf-8');
    assert.ok(content.includes('claude.com/blog/skills'), 'Should include Agent Skills post');
  });
});

describe('RSS Feed - Valid XML', () => {
  it('should have balanced opening and closing tags for key elements', () => {
    const content = fs.readFileSync(RSS_PATH, 'utf-8');
    const tagsToCheck = ['rss', 'channel', 'title', 'link', 'description', 'language'];
    for (const tag of tagsToCheck) {
      const openCount = (content.match(new RegExp(`<${tag}[\\s>]`, 'g')) || []).length;
      const closeCount = (content.match(new RegExp(`</${tag}>`, 'g')) || []).length;
      // Self-closing tags (like atom:link) are excluded from this check
      assert.ok(
        openCount >= closeCount,
        `Tag <${tag}> should have balanced open (${openCount}) and close (${closeCount}) counts`
      );
    }
  });

  it('should be well-formed (no unclosed item tags)', () => {
    const content = fs.readFileSync(RSS_PATH, 'utf-8');
    const openItems = (content.match(/<item>/g) || []).length;
    const closeItems = (content.match(/<\/item>/g) || []).length;
    assert.equal(openItems, closeItems, 'Should have equal number of <item> and </item> tags');
  });

  it('should not contain HTML entities that need escaping in invalid positions', () => {
    const content = fs.readFileSync(RSS_PATH, 'utf-8');
    // Check that content between tags doesn't have unescaped & (except valid entities)
    const textBlocks = content.match(/>([^<]+)</g) || [];
    for (const block of textBlocks) {
      const text = block.slice(1, -1); // remove > and <
      const unescapedAmps = text.match(/&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[\da-fA-F]+;)/g);
      assert.ok(
        !unescapedAmps,
        `Found unescaped ampersand in: "${text.substring(0, 50)}..."`
      );
    }
  });
});
