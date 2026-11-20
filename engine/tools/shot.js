// The kit's only renderer.
//   node tools/shot.js <file or url> --widths 1440,390 [--out <dir>] [--name <name>] [--first]
// Writes <name>-<w>.png (full page, for boards) and <name>-<w>-m.png (the first screen at 1000px or less on its
// long side: the only copy a model may view). --first writes only <name>-<w>-first.png (first screen, full size,
// for the gate frames). Fails (exit 1) when the page does not load.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : d; };
const src = a[0];
if (!src || src.startsWith('--')) { console.log('usage: node tools/shot.js <file|url> --widths 1440,390 [--out dir] [--name n] [--first]'); process.exit(1); }
const url = /^https?:|^file:/.test(src) ? src : 'file://' + path.resolve(src);
const widths = opt('--widths', '1440,390').split(',').map(Number);
const out = path.resolve(opt('--out', path.join(path.dirname(path.resolve(src)), 'png')));
const name = opt('--name', path.basename(src).replace(/\.html?$/, ''));
const first = a.includes('--first'); const MAXPX = 1000; const SCREEN = 900;
fs.mkdirSync(out, { recursive: true });
(async () => {
  // Remote pages go through the workspace's proxy (Chromium ignores HTTPS_PROXY on its own). The proxy re-signs
  // TLS with its own CA, so certificate errors are ignored for captures only. Local files never use the proxy.
  const remote = /^https?:/.test(url); const px = process.env.HTTPS_PROXY || process.env.https_proxy;
  const b = await chromium.launch(remote && px ? { proxy: { server: px } } : {}); const made = [];
  // Local pages: a stored consent choice (nothing allowed) keeps the consent banner off the captures; comply.py tests it.
  const ctx = async (o) => { const c = await b.newContext({ ...o, ignoreHTTPSErrors: !!(remote && px) });
    if (!remote) await c.addInitScript(() => { try { if (!localStorage.getItem('k-consent')) localStorage.setItem('k-consent', JSON.stringify({ v: 1, time: '', gpc: false })); } catch (e) { } });
    return c; };
  for (const w of widths) {
    const p = await (await ctx({ viewport: { width: w, height: SCREEN }, reducedMotion: 'reduce' })).newPage();
    let err = ''; const r = await p.goto(url, { waitUntil: 'load', timeout: 45000 }).catch(e => { err = String(e); return null; });
    if (!r && remote) {
      console.log('shot: page did not load: ' + src + (/TUNNEL|PROXY|403/.test(err) ? ' (blocked by the environment\'s network access: set it to Full, or add this domain under Custom; or ask the CD for screenshots)' : ' ' + err.slice(0, 120)));
      process.exit(1);
    }
    await p.evaluate(() => document.fonts && document.fonts.ready); await p.waitForTimeout(120);
    if (first) { const f = path.join(out, `${name}-${w}-first.png`); await p.screenshot({ path: f }); made.push(f); await p.close(); continue; }
    const full = path.join(out, `${name}-${w}.png`); await p.screenshot({ path: full, fullPage: true }); made.push(full);
    await p.close();
    const scale = Math.min(1, MAXPX / Math.max(w, SCREEN));
    const c = await ctx({ viewport: { width: w, height: SCREEN }, deviceScaleFactor: scale, reducedMotion: 'reduce' });
    const q = await c.newPage(); await q.goto(url, { waitUntil: 'load' }).catch(() => {}); await q.waitForTimeout(120);
    const m = path.join(out, `${name}-${w}-m.png`); await q.screenshot({ path: m }); made.push(m); await c.close();
  }
  await b.close();
  console.log(`shot: ${made.length} file(s) in ${path.relative(process.cwd(), out) || '.'}: ` + made.map(f => path.basename(f)).join(' '));
})().catch(e => { console.log('shot: ' + String(e).slice(0, 200)); process.exit(1); });
