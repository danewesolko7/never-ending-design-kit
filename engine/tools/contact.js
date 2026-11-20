// One labelled contact sheet from a set of PNGs, 1000px or less on its long side (the only size a model views).
//   node tools/contact.js <out.png> <png> [more ...] [--w 200] [--hmax 1500] [--cols N]
// Draws in Chromium's canvas (playwright, already pinned for shot.js), so the kit needs no Python imaging library.
// contact.py wraps this (glob expansion, the render event) and is what the other tools call.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const a = process.argv.slice(2);
if (a.length < 2 || a[0] === '-h' || a[0] === '--help') {
  console.log('usage: node tools/contact.js <out.png> <png> [more ...] [--w 200] [--hmax 1500] [--cols N]'); process.exit(a.length < 2 ? 1 : 0);
}
const opts = { '--w': 200, '--hmax': 1500, '--cols': 0 }; const files = []; const out = path.resolve(a[0]);
for (let i = 1; i < a.length; i++) {
  if (a[i] in opts) { opts[a[i]] = parseInt(a[++i], 10); continue; }
  const f = path.resolve(a[i]);
  if (f.toLowerCase().endsWith('.png') && f !== out && fs.existsSync(f) && !files.includes(f)) files.push(f);
}
if (!files.length) { console.log('contact: no PNGs matched'); process.exit(0); }
const MAX = 1000;
(async () => {
  const b = await chromium.launch();
  try {
    const page = await b.newPage();
    const imgs = files.map(f => ({ name: path.basename(f, path.extname(f)), src: 'data:image/png;base64,' + fs.readFileSync(f).toString('base64') }));
    const res = await page.evaluate(async ({ imgs, W, HM, COLS, MAX }) => {
      const load = (src) => new Promise((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => no(new Error('bad png')); i.src = src; });
      const gap = 12, lab = 22;
      const tiles = [];
      for (const t of imgs) { const im = await load(t.src); const h = Math.round(im.naturalHeight * W / im.naturalWidth); tiles.push({ name: t.name, im, h, ch: Math.min(h, HM) }); }
      const cols = COLS || Math.max(1, Math.min(tiles.length, Math.floor((1560 - gap) / (W + gap))));
      const rows = []; for (let k = 0; k < tiles.length; k += cols) rows.push(tiles.slice(k, k + cols));
      const rh = rows.map(r => Math.max(...r.map(t => t.ch)) + lab);
      const SW = gap + cols * (W + gap), SH = gap + rh.reduce((s, h) => s + h + gap, 0);
      const c = document.createElement('canvas'); c.width = SW; c.height = SH; const x = c.getContext('2d');
      x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
      x.fillStyle = 'rgb(136,136,136)'; x.fillRect(0, 0, SW, SH);
      x.font = '14px "DejaVu Sans", Arial, sans-serif'; x.textBaseline = 'top'; x.fillStyle = '#fff';
      let y = gap;
      rows.forEach((r, ri) => {
        let xx = gap;
        for (const t of r) {
          // the tile is the image scaled to W wide, cropped at the top to HM tall
          const srcH = t.ch * t.im.naturalWidth / W;
          x.drawImage(t.im, 0, 0, t.im.naturalWidth, srcH, xx, y, W, t.ch);
          x.fillText(t.name.slice(0, 28), xx, y + t.ch + 4); xx += W + gap;
        }
        y += rh[ri] + gap;
      });
      const s = Math.min(1, MAX / Math.max(SW, SH)); let f = c;
      if (s < 1) {
        f = document.createElement('canvas'); f.width = Math.round(SW * s); f.height = Math.round(SH * s);
        const fx = f.getContext('2d'); fx.imageSmoothingEnabled = true; fx.imageSmoothingQuality = 'high'; fx.drawImage(c, 0, 0, f.width, f.height);
      }
      return { w: f.width, h: f.height, n: tiles.length, data: f.toDataURL('image/png').split(',')[1] };
    }, { imgs, W: opts['--w'], HM: opts['--hmax'], COLS: opts['--cols'], MAX });
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, Buffer.from(res.data, 'base64'));
    console.log(`contact: ${a[0]} ${res.w}x${res.h}, ${res.n} tiles, about ${Math.floor(res.w * res.h / 750)} image tokens`);
  } finally { await b.close(); }
})().catch(e => { console.error('contact: ' + e.message); process.exit(1); });
