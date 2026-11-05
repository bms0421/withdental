// Renders each built page once (no timers) and returns its markup plus FAQ text.
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const root = process.argv[2];
const files = process.argv.slice(3);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.jpg': 'image/jpeg', '.css': 'text/css' };

const server = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(root, p);
  if (!f.startsWith(root) || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
  fs.createReadStream(f).pipe(res);
});

(async () => {
  await new Promise((r) => server.listen(0, r));
  const port = server.address().port;
  const browser = await chromium.launch();
  const out = {};
  for (const file of files) {
    const page = await browser.newPage();
    // block network beyond the local server (fonts, maps)
    await page.route('**/*', (route) => route.request().url().startsWith('http://localhost:' + port) ? route.continue() : route.abort());
    await page.addInitScript(() => {
      const realBoot = () => {};
      Object.defineProperty(window, 'WD', {
        configurable: true,
        set(v) {
          const boot = v.boot;
          v.boot = function (C, props) {
            const proto = C.prototype;
            delete proto.componentDidMount;
            proto.componentDidMount = undefined;
            return boot.call(this, C, props);
          };
          Object.defineProperty(window, 'WD', { value: v, writable: true, configurable: true });
        },
        get() { return undefined; }
      });
    });
    const rel = '/' + path.relative(root, file).replace(/index\.html$/, '');
    await page.goto('http://localhost:' + port + rel, { waitUntil: 'domcontentloaded' });
    const data = await page.evaluate(() => {
      const r = document.getElementById('wd-root');
      const faq = Array.from(document.querySelectorAll('#faq details, .inv-faq details')).map((d) => {
        const q = d.querySelector('summary');
        const qt = q ? q.textContent.replace(/\s+/g, ' ').trim() : '';
        const clone = d.cloneNode(true);
        const s = clone.querySelector('summary');
        if (s) s.remove();
        return [qt, clone.textContent.replace(/\s+/g, ' ').trim()];
      }).filter((x) => x[0] && x[1]);
      return { html: r.innerHTML, faq };
    });
    out[file] = data;
    await page.close();
  }
  await browser.close();
  server.close();
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(1); });
