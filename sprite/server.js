const http = require('node:http');
const https = require('node:https');

const PORT = parseInt(process.env.PORT, 10) || 8080;
const CACHE_TTL_MS = 60_000; // 1-minute debounce

// ---------------------------------------------------------------------------
// In-memory cache
// ---------------------------------------------------------------------------
const cache = {};

function getCached(key) {
  const entry = cache[key];
  if (!entry) return null;
  if (Date.now() - entry.ts < CACHE_TTL_MS) return entry.data;
  return null;
}

function setCache(key, data) {
  cache[key] = { data, ts: Date.now() };
}

// ---------------------------------------------------------------------------
// Lightweight HTTPS fetch (no dependencies)
// ---------------------------------------------------------------------------
function fetch(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'User-Agent': 'SpriteFeedBot/1.0' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return fetch(res.headers.location).then(resolve, reject);
      }
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('end', () => resolve(body));
    });
    req.on('error', reject);
    req.setTimeout(10_000, () => { req.destroy(); reject(new Error('timeout')); });
  });
}

// ---------------------------------------------------------------------------
// Scrapers
// ---------------------------------------------------------------------------

// Scrape claude.com/blog/category/announcements
// The page is Webflow-rendered so we look for og / meta / structured data and
// any <a> elements whose href matches /blog/ patterns.
async function scrapeClaudeAnnouncements() {
  const html = await fetch('https://claude.com/blog/category/announcements');
  const items = [];

  // Try to extract links + titles from anchor tags referencing /blog/
  const linkRe = /<a[^>]+href=["']([^"']*\/blog\/[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = linkRe.exec(html)) !== null) {
    const href = m[1].startsWith('http') ? m[1] : `https://claude.com${m[1]}`;
    const text = m[2].replace(/<[^>]+>/g, '').trim();
    if (text && !items.some((i) => i.link === href)) {
      items.push({ title: text, link: href, description: '' });
    }
  }
  return items;
}

// Scrape anthropic.com/news
async function scrapeAnthropicNews() {
  const html = await fetch('https://www.anthropic.com/news');
  const items = [];

  const linkRe = /<a[^>]+href=["']([^"']*\/news\/[^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = linkRe.exec(html)) !== null) {
    const href = m[1].startsWith('http') ? m[1] : `https://www.anthropic.com${m[1]}`;
    const text = m[2].replace(/<[^>]+>/g, '').trim();
    if (text && text.length > 3 && !items.some((i) => i.link === href)) {
      items.push({ title: text, link: href, description: '' });
    }
  }
  return items;
}

// ---------------------------------------------------------------------------
// Seed data (used as baseline and fallback)
// ---------------------------------------------------------------------------

const CLAUDE_ANNOUNCEMENTS = [
  { title: 'Customize Claude Code with plugins', link: 'https://claude.com/blog/claude-code-plugins', pubDate: 'Thu, 30 Jan 2026 00:00:00 GMT', description: 'Claude Code now supports plugins\u2014customizable collections of slash commands, agents, MCP servers, and hooks that users can install with a single command to share standardized setups and enforce coding standards.' },
  { title: "Understand Claude Code's impact with contribution metrics", link: 'https://claude.com/blog/contribution-metrics', pubDate: 'Wed, 29 Jan 2026 00:00:00 GMT', description: 'Claude Code now offers contribution metrics in public beta, enabling engineering teams to measure velocity by tracking pull requests merged and code committed with AI assistance.' },
  { title: 'Updates to Claude Team', link: 'https://claude.com/blog/claude-team-updates', pubDate: 'Tue, 28 Jan 2026 00:00:00 GMT', description: 'The Claude Team plan is now more accessible with lower pricing for standard and premium seats, new annual discounts, and collaborative workspace features including Claude Code integration.' },
  { title: 'Your favorite work tools are now interactive inside Claude', link: 'https://claude.com/blog/interactive-tools-in-claude', pubDate: 'Mon, 26 Jan 2026 00:00:00 GMT', description: 'Claude now offers interactive tool integration built on the open Model Context Protocol (MCP), allowing users to open and interact with tools like Asana, Slack, and Figma directly within conversations.' },
  { title: 'Cowork: Claude Code for the rest of your work', link: 'https://claude.com/blog/cowork-research-preview', pubDate: 'Mon, 12 Jan 2026 00:00:00 GMT', description: "Cowork extends Claude's agentic capabilities beyond coding to general users, allowing them to grant Claude access to computer folders to read, edit, and create files for tasks like organizing documents and creating spreadsheets." },
  { title: "Extending Claude's capabilities with skills and MCP servers", link: 'https://claude.com/blog/extending-claude-capabilities-with-skills-mcp-servers', pubDate: 'Fri, 19 Dec 2025 00:00:00 GMT', description: 'Model Context Protocol connects Claude to third-party tools, and skills teach Claude how to use them well, enabling teams to build agents that follow custom workflows.' },
  { title: "What's new in Claude: Turning Claude into your thinking partner", link: 'https://claude.com/blog/your-thinking-partner', pubDate: 'Thu, 20 Nov 2025 00:00:00 GMT', description: 'Claude has introduced new features including memory, voice capabilities, and file creation that enable it to function as a collaborative thinking partner, maintaining context across conversations.' },
  { title: 'Claude Code on the web', link: 'https://claude.com/blog/claude-code-on-the-web', pubDate: 'Wed, 12 Nov 2025 00:00:00 GMT', description: 'Developers can now assign multiple coding tasks that execute on cloud infrastructure, connect GitHub repositories, run tasks in parallel, and automatically generate pull requests with change summaries.' },
  { title: 'Introducing Agent Skills', link: 'https://claude.com/blog/skills', pubDate: 'Thu, 16 Oct 2025 00:00:00 GMT', description: "Claude now features Skills\u2014customizable folders containing instructions, scripts, and resources that enable Claude to perform specialized tasks more effectively across Claude apps, Claude Code, and the API." },
  { title: 'Customize Claude Code with plugins', link: 'https://claude.com/blog/claude-code-plugins', pubDate: 'Thu, 09 Oct 2025 00:00:00 GMT', description: 'Claude Code now supports plugins\u2014customizable collections of slash commands, agents, MCP servers, and hooks that users can install with a single command.' },
  { title: 'Claude and Slack', link: 'https://claude.com/blog/claude-and-slack', pubDate: 'Wed, 01 Oct 2025 00:00:00 GMT', description: 'Anthropic introduced two ways to integrate Claude with Slack: adding Claude directly to workspaces for real-time assistance, or connecting Slack to Claude for searching channels, messages, and files.' },
  { title: 'Claude is now available in Microsoft 365 Copilot', link: 'https://claude.com/blog/claude-now-available-in-microsoft-365-copilot', pubDate: 'Wed, 24 Sep 2025 00:00:00 GMT', description: 'Claude models including Sonnet 4 and Opus 4.1 are now accessible through Microsoft 365 Copilot, giving enterprise customers enhanced flexibility in selecting AI models for their workflows.' },
  { title: 'Build and share AI-powered apps with Claude', link: 'https://claude.com/blog/claude-powered-artifacts', pubDate: 'Fri, 25 Jul 2025 00:00:00 GMT', description: 'Developers can now create and host interactive AI-powered apps directly within the Claude platform, where users authenticate with their own accounts and API usage counts against their own subscriptions.' },
  { title: 'Claude can now connect to your world', link: 'https://claude.com/blog/integrations', pubDate: 'Thu, 01 May 2025 00:00:00 GMT', description: 'Anthropic launched Integrations enabling Claude to connect with remote MCP servers from popular tools like Jira, Zapier, and Asana, with expanded Research capabilities.' },
  { title: 'Introducing the Max Plan', link: 'https://claude.com/blog/max-plan', pubDate: 'Wed, 09 Apr 2025 00:00:00 GMT', description: "Claude's Max plan provides up to 20x higher usage limits than Pro at $100 and $200 monthly tiers, with priority access to new features and models." },
];

const ANTHROPIC_NEWS = [
  { title: 'Claude is a space to think', link: 'https://www.anthropic.com/news/claude-is-a-space-to-think', pubDate: 'Wed, 04 Feb 2026 00:00:00 GMT', description: 'Anthropic announces Claude will remain ad-free, explaining why advertising incentives are incompatible with a genuinely helpful AI assistant.' },
  { title: "Apple's Xcode now supports the Claude Agent SDK", link: 'https://www.anthropic.com/news/apple-xcode-claude-agent-sdk', pubDate: 'Tue, 03 Feb 2026 00:00:00 GMT', description: "Apple's Xcode integrates the Claude Agent SDK, enabling developers to build AI-powered applications within Apple's development ecosystem." },
  { title: 'Anthropic partners with Allen Institute and Howard Hughes Medical Institute to accelerate scientific discovery', link: 'https://www.anthropic.com/news/anthropic-partners-with-allen-institute-and-howard-hughes-medical-institute', pubDate: 'Mon, 02 Feb 2026 00:00:00 GMT', description: 'Anthropic partners with leading research institutions to apply Claude to accelerate breakthroughs in biological and biomedical sciences.' },
  { title: 'Claude on Mars', link: 'https://www.anthropic.com/mars', pubDate: 'Fri, 30 Jan 2026 00:00:00 GMT', description: "The first AI-assisted drive on another planet. Claude helped NASA's Perseverance rover travel four hundred meters on Mars." },
  { title: 'ServiceNow chooses Claude to power customer apps and increase internal productivity', link: 'https://www.anthropic.com/news/servicenow-anthropic-claude', pubDate: 'Wed, 28 Jan 2026 00:00:00 GMT', description: 'ServiceNow selects Claude to enhance customer applications and boost internal productivity across the enterprise platform.' },
  { title: 'Anthropic partners with the UK Government to bring AI assistance to GOV.UK services', link: 'https://www.anthropic.com/news/gov-UK-partnership', pubDate: 'Mon, 27 Jan 2026 00:00:00 GMT', description: 'Anthropic and the UK Government deploy a Claude-powered AI assistant on GOV.UK to guide citizens through government processes.' },
  { title: "Claude's new constitution", link: 'https://www.anthropic.com/news/claude-new-constitution', pubDate: 'Thu, 22 Jan 2026 00:00:00 GMT', description: "Anthropic publishes a new version of Claude's constitution, the explicit set of values and principles that guide Claude's behavior through Constitutional AI." },
  { title: "Mariano-Florentino Cu\u00e9llar appointed to Anthropic's Long-Term Benefit Trust", link: 'https://www.anthropic.com/news/mariano-florentino-long-term-benefit-trust', pubDate: 'Wed, 21 Jan 2026 00:00:00 GMT', description: "Mariano-Florentino Cu\u00e9llar, former Justice of the Supreme Court of California, joins Anthropic's governance body overseeing the company's public benefit mission." },
  { title: 'Anthropic and Teach For All launch global AI training initiative for educators', link: 'https://www.anthropic.com/news/anthropic-teach-for-all', pubDate: 'Wed, 21 Jan 2026 00:00:00 GMT', description: 'Anthropic partners with Teach For All to bring AI literacy and training to educators worldwide, supporting responsible AI adoption in education.' },
  { title: 'Anthropic appoints Irina Ghose as Managing Director of India', link: 'https://www.anthropic.com/news/anthropic-appoints-irina-ghose-as-managing-director-of-india', pubDate: 'Fri, 16 Jan 2026 00:00:00 GMT', description: 'Anthropic names Irina Ghose as Managing Director of India ahead of opening its Bengaluru office, expanding operations in the Asia Pacific region.' },
  { title: 'How scientists are using Claude to accelerate research and discovery', link: 'https://www.anthropic.com/news/accelerating-scientific-research', pubDate: 'Thu, 15 Jan 2026 00:00:00 GMT', description: 'Scientists across disciplines use Claude to analyze data, generate hypotheses, and accelerate the pace of research and discovery.' },
  { title: 'Introducing Claude Opus 4.5', link: 'https://www.anthropic.com/news/claude-opus-4-5', pubDate: 'Mon, 24 Nov 2025 00:00:00 GMT', description: 'The best model in the world for coding, agents, and computer use, with meaningful improvements to everyday tasks and dramatic token efficiency gains.' },
  { title: 'Snowflake and Anthropic announce $200 million partnership', link: 'https://www.anthropic.com/news/snowflake-anthropic-expanded-partnership', pubDate: 'Wed, 03 Dec 2025 00:00:00 GMT', description: 'A multi-year $200 million agreement to make Claude models available across Snowflake\u2019s platform to more than 12,600 global customers.' },
  { title: 'Introducing Claude Sonnet 4.5', link: 'https://www.anthropic.com/news/claude-sonnet-4-5', pubDate: 'Mon, 29 Sep 2025 00:00:00 GMT', description: 'Sets new benchmark records in coding, reasoning, and computer use while being the most aligned frontier model, released under ASL-3 protections.' },
  { title: 'Introducing Claude Haiku 4.5', link: 'https://www.anthropic.com/news/claude-haiku-4-5', pubDate: 'Wed, 15 Oct 2025 00:00:00 GMT', description: 'Matches state-of-the-art coding capabilities while delivering unprecedented speed and cost-efficiency for high-throughput applications.' },
  { title: 'A statement from Dario Amodei on American AI leadership', link: 'https://www.anthropic.com/news/statement-dario-amodei-american-ai-leadership', pubDate: 'Tue, 21 Oct 2025 00:00:00 GMT', description: "Anthropic CEO Dario Amodei outlines the company's commitment to advancing America's leadership in building powerful and beneficial AI." },
  { title: 'Anthropic expands global operations to India', link: 'https://www.anthropic.com/news/expanding-global-operations-to-india', pubDate: 'Tue, 07 Oct 2025 00:00:00 GMT', description: "Anthropic announces plans to open an office in Bengaluru, India, its second in Asia Pacific, to serve India's rapidly growing AI ecosystem." },
  { title: 'Accenture and Anthropic launch multi-year partnership', link: 'https://www.anthropic.com/news/anthropic-accenture-partnership', pubDate: 'Tue, 09 Dec 2025 00:00:00 GMT', description: 'Initial solutions target regulated industries with approximately 30,000 Accenture professionals trained on Claude for enterprise transformation.' },
  { title: 'Anthropic Economic Futures Program Launch', link: 'https://www.anthropic.com/news/introducing-the-anthropic-economic-futures-program', pubDate: 'Mon, 01 Sep 2025 00:00:00 GMT', description: "A new initiative to support research and policy development focused on addressing AI's economic impacts and understanding how AI is reshaping work." },
  { title: 'Expanding our model safety bug bounty program', link: 'https://www.anthropic.com/news/model-safety-bug-bounty', pubDate: 'Wed, 20 Aug 2025 00:00:00 GMT', description: 'Anthropic expands its bug bounty program with rewards up to $15,000 for novel universal jailbreak attacks that expose vulnerabilities in critical risk areas.' },
];

// ---------------------------------------------------------------------------
// RSS generation
// ---------------------------------------------------------------------------

function escapeXml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function buildRss({ title, siteLink, description, selfLink, items }) {
  const itemsXml = items
    .map(
      (i) => `    <item>
      <title>${escapeXml(i.title)}</title>
      <link>${escapeXml(i.link)}</link>
      <guid isPermaLink="true">${escapeXml(i.link)}</guid>
      ${i.pubDate ? `<pubDate>${i.pubDate}</pubDate>` : ''}
      <description>${escapeXml(i.description || '')}</description>
    </item>`
    )
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${escapeXml(title)}</title>
    <link>${escapeXml(siteLink)}</link>
    <description>${escapeXml(description)}</description>
    <language>en-us</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${escapeXml(selfLink)}" rel="self" type="application/rss+xml"/>
${itemsXml}
  </channel>
</rss>`;
}

// ---------------------------------------------------------------------------
// Feed builders (scrape + merge with seed data, cached)
// ---------------------------------------------------------------------------

async function getClaudeAnnouncementsFeed(baseUrl) {
  const key = 'claude-announcements';
  const cached = getCached(key);
  if (cached) return cached;

  let items = [...CLAUDE_ANNOUNCEMENTS];
  try {
    const scraped = await scrapeClaudeAnnouncements();
    // Merge scraped items that aren't already in seed data
    for (const s of scraped) {
      if (!items.some((i) => i.link === s.link)) {
        items.unshift(s);
      }
    }
  } catch {
    // Fall back to seed data on scrape failure
  }

  // Deduplicate by link
  const seen = new Set();
  items = items.filter((i) => {
    if (seen.has(i.link)) return false;
    seen.add(i.link);
    return true;
  });

  const xml = buildRss({
    title: 'Claude Product Announcements',
    siteLink: 'https://claude.com/blog/category/announcements',
    description: 'Stay up to date on the latest Claude features, model releases, and product updates from Anthropic.',
    selfLink: `${baseUrl}/feed/announcements.xml`,
    items,
  });

  setCache(key, xml);
  return xml;
}

async function getAnthropicNewsFeed(baseUrl) {
  const key = 'anthropic-news';
  const cached = getCached(key);
  if (cached) return cached;

  let items = [...ANTHROPIC_NEWS];
  try {
    const scraped = await scrapeAnthropicNews();
    for (const s of scraped) {
      if (!items.some((i) => i.link === s.link)) {
        items.unshift(s);
      }
    }
  } catch {
    // Fall back to seed data on scrape failure
  }

  const seen = new Set();
  items = items.filter((i) => {
    if (seen.has(i.link)) return false;
    seen.add(i.link);
    return true;
  });

  const xml = buildRss({
    title: 'Anthropic News',
    siteLink: 'https://www.anthropic.com/news',
    description: 'The latest news, announcements, partnerships, and research updates from Anthropic.',
    selfLink: `${baseUrl}/feed/anthropic-news.xml`,
    items,
  });

  setCache(key, xml);
  return xml;
}

// ---------------------------------------------------------------------------
// HTTP server
// ---------------------------------------------------------------------------

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const baseUrl = `https://${req.headers.host || 'localhost'}`;

  try {
    if (url.pathname === '/feed/announcements.xml') {
      const xml = await getClaudeAnnouncementsFeed(baseUrl);
      res.writeHead(200, { 'Content-Type': 'application/rss+xml; charset=utf-8', 'Cache-Control': 'public, max-age=60' });
      res.end(xml);
    } else if (url.pathname === '/feed/anthropic-news.xml') {
      const xml = await getAnthropicNewsFeed(baseUrl);
      res.writeHead(200, { 'Content-Type': 'application/rss+xml; charset=utf-8', 'Cache-Control': 'public, max-age=60' });
      res.end(xml);
    } else if (url.pathname === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(`<!DOCTYPE html>
<html><head><title>RSS Feeds</title></head>
<body>
<h1>RSS Feeds</h1>
<ul>
  <li><a href="/feed/announcements.xml">Claude Product Announcements</a></li>
  <li><a href="/feed/anthropic-news.xml">Anthropic News</a></li>
</ul>
</body></html>`);
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
    }
  } catch (err) {
    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end('Internal Server Error');
  }
});

server.listen(PORT, () => {
  console.log(`RSS feed server listening on port ${PORT}`);
});
