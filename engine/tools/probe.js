// Browser probe for pass.py and greek.py: loads each page at each width and returns findings as JSON.
//   node tools/probe.js '<json config>'
// config: {files:[abs paths], widths:[1440,768,390,320], mode:"page"|"rough"|"system", expansion:1.3, artboard:8000}
// Findings: {page, width, check, detail}. Checks: overflow, axe (AAA), widow, overlap, target, meta, heading, code,
// expansion, motion, height, rules (stacked rules), numerals (figure styles). Prints one JSON object to stdout; pass.py summarises it.
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
const cfg = JSON.parse(process.argv[2] || '{}');
// WCAG 2.2 AAA by default; a brief may set "wcag": "AA" (pass.py passes it as cfg.wcag)
const TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'].concat(cfg.wcag === 'AA' ? [] : ['wcag2aaa']);
let axeSrc = null;
for (const base of [process.env.KIT_NODE, path.join(__dirname, 'node_modules')].filter(Boolean)) {
  const f = path.join(base, 'axe-core', 'axe.min.js'); if (fs.existsSync(f)) { axeSrc = fs.readFileSync(f, 'utf8'); break; }
}
(async () => {
  const b = await chromium.launch(); const out = []; const info = {};
  const add = (page, width, check, detail) => out.push({ page, width, check, detail: String(detail).slice(0, 160) });
  for (const file of cfg.files) {
    const name = path.basename(file, '.html'); info[name] = {};
    for (const w of cfg.widths) {
      const p = await b.newPage({ viewport: { width: w, height: 900 }, reducedMotion: 'reduce' });
      await p.goto('file://' + file); await p.waitForTimeout(150);
      const r = await p.evaluate(({ w, mode }) => {
        const o = { overflow: document.documentElement.scrollWidth > w + 1, widows: [], overlaps: [], targets: [], height: Math.ceil(document.documentElement.scrollHeight) };
        const txtSel = mode === 'rough' ? '.gk-t' : 'main p,main li,main h1,main h2,main h3,main h4,main figcaption,main dd,main blockquote';
        if (mode !== 'rough') {
          for (const el of document.querySelectorAll('main p,main li,main h1,main h2,main h3,main figcaption,main dd')) {
            if (el.querySelector('p,li,ul,div') || el.textContent.trim().split(/\s+/).length < 3) continue;
            const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const ws = [];
            while (tw.nextNode()) { const t = tw.currentNode; const re = /[^\s ]+( [^\s ]+)*/g; let m;
              while ((m = re.exec(t.data))) { const rr = document.createRange(); rr.setStart(t, m.index); rr.setEnd(t, m.index + m[0].length); const rc = rr.getClientRects(); if (rc.length) { const q = rc[rc.length - 1]; ws.push([q.top, q.bottom, m[0]]); } } }
            if (ws.length < 2) continue;
            const same = (a, c) => a[0] < c[1] - 2 && c[0] < a[1] - 2; const last = ws[ws.length - 1];
            const onLast = ws.filter(x => same(x, last)).length; const multi = ws.some(x => !same(x, last));
            if (multi && onLast === 1 && !/ /.test(last[2])) o.widows.push(el.textContent.trim().slice(-40));
          }
        }
        const blocks = [...document.querySelectorAll(mode === 'rough' ? '.gk-sec' : 'main>*')].map(e => [e, e.getBoundingClientRect()]);
        const imgs = [...document.querySelectorAll(mode === 'rough' ? '.gk-i' : 'main img, main picture, main video')].map(i => [i.getBoundingClientRect(), i]);
        for (const el of document.querySelectorAll(txtSel)) {
          const r = el.getBoundingClientRect(); if (!r.height || !r.width) continue;
          const own = el.closest(mode === 'rough' ? '.gk-sec' : 'main>*');
          for (const [blk, br] of blocks) if (blk !== own && r.bottom > br.top + 1 && r.top < br.bottom - 1 && r.right > br.left && r.left < br.right) { o.overlaps.push('crosses section: ' + (el.textContent.trim().slice(0, 30) || el.className)); break; }
          for (const [ir, im] of imgs) if (!el.contains(im) && !im.contains(el) && r.bottom > ir.top + 1 && r.top < ir.bottom - 1 && r.right > ir.left + 1 && r.left < ir.right - 1) { o.overlaps.push('on image: ' + (el.textContent.trim().slice(0, 30) || el.className)); break; }
        }
        if (mode !== 'rough') for (const a of document.querySelectorAll('a,button,input,select,textarea')) {
          if (a.classList.contains('k-skip')) continue;
          const par = a.parentElement; const inline = par && /^(P|LI|DD|SPAN|FIGCAPTION|TD)$/.test(par.tagName) && par.textContent.trim().length > a.textContent.trim().length + 3;
          const q = a.getBoundingClientRect(); if (!inline && q.width && (q.height < 44 || q.width < 44)) o.targets.push(`${a.tagName.toLowerCase()} "${a.textContent.trim().slice(0, 24)}" ${Math.round(q.width)}x${Math.round(q.height)}`);
        }
        return o;
      }, { w, mode: cfg.mode });
      if (r.overflow) add(name, w, 'overflow', `horizontal scroll at ${w}px`);
      for (const x of r.widows) add(name, w, 'widow', x);
      for (const x of [...new Set(r.overlaps)]) add(name, w, 'overlap', x);
      for (const x of [...new Set(r.targets)]) add(name, w, 'target', x + ' (under 44px)');
      if (w === 1440 || w === cfg.widths[0]) { info[name].height = r.height; if (r.height > (cfg.artboard || 8000)) add(name, w, 'height', `${r.height}px tall, over the ${cfg.artboard || 8000}px artboard (warning)`); }
      if (cfg.mode !== 'rough' && axeSrc && (w === 1440 || w === 390)) {
        await p.addScriptTag({ content: axeSrc });
        const v = await p.evaluate(async (TAGS) => (await axe.run(document, { runOnly: { type: 'tag', values: TAGS } })).violations.map(v => [v.id, v.nodes.length, (v.nodes[0] || {}).target]), TAGS);
        for (const [id, n, t] of v) add(name, w, 'axe', `${id} x${n} ${JSON.stringify(t || '')}`);
      } else if (cfg.mode !== 'rough' && !axeSrc && w === cfg.widths[0]) add(name, w, 'axe', 'axe-core not installed: run tools/setup.sh');
      if (cfg.mode !== 'rough' && w === cfg.widths[0]) {
        const m = await p.evaluate(() => {
          const g = s => (document.querySelector(s) || {}).content || '';
          const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => +h.tagName[1]);
          const skips = []; for (let i = 1; i < hs.length; i++) if (hs[i] > hs[i - 1] + 1) skips.push(`h${hs[i - 1]}->h${hs[i]}`);
          const badClass = new Set(); for (const e of document.querySelectorAll('[class]')) for (const c of e.classList) if (!/^[a-z][a-z0-9]*-[a-z0-9-]+$/.test(c)) badClass.add(c);
          return { title: document.title, desc: g('meta[name="description"]'), ogt: g('meta[property="og:title"]'), ogd: g('meta[property="og:description"]'),
            ogi: g('meta[property="og:image"]'), lang: document.documentElement.lang, h1: document.querySelectorAll('h1').length, skips,
            inline: document.querySelectorAll('[style]').length, styleTags: document.querySelectorAll('style').length,
            sheets: document.querySelectorAll('link[rel="stylesheet"]').length, badClass: [...badClass].slice(0, 6), landmarks: !!document.querySelector('main') && !!document.querySelector('header') && !!document.querySelector('footer'),
            imgs: [...document.querySelectorAll('img')].filter(i => !i.hasAttribute('alt') || !i.getAttribute('width') || !i.getAttribute('height')).length,
            lazy: [...document.querySelectorAll('img')].slice(1).filter(i => i.getAttribute('loading') !== 'lazy').length,
            // rules: two horizontal rules within 8px of each other in the same column read as one doubled rule
            stacked: (() => { const hs = []; for (const e of document.querySelectorAll('main *')) { const c = getComputedStyle(e); const r = e.getBoundingClientRect(); if (!r.width) continue;
                if (parseFloat(c.borderTopWidth) > 0 && c.borderTopStyle !== 'none') hs.push([r.top, r.left, r.right, e]);
                if (parseFloat(c.borderBottomWidth) > 0 && c.borderBottomStyle !== 'none') hs.push([r.bottom, r.left, r.right, e]); }
              const o2 = new Set(); for (let i = 0; i < hs.length; i++) for (let j = i + 1; j < hs.length; j++) { const a = hs[i], c2 = hs[j];
                if (a[3] !== c2[3] && Math.abs(a[0] - c2[0]) > 1 && Math.abs(a[0] - c2[0]) < 8 && Math.min(a[2], c2[2]) - Math.max(a[1], c2[1]) > 40) o2.add((a[3].className || a[3].tagName) + ' / ' + (c2[3].className || c2[3].tagName)); }
              return [...o2].slice(0, 4); })(),
            // numerals: figures (prices, licence, rating, phone) in more than one face + numeral setting (mono labels exempt)
            figs: (() => { const st = new Set(); for (const e of document.querySelectorAll('main *, header *')) { if (e.children.length) continue; const t = e.textContent.trim();
                if (t.length < 3 || !/^[\d$€£+().,\/\s-]+$/.test(t) || !/\d{2}/.test(t)) continue; const c = getComputedStyle(e);
                if (/mono/i.test(c.fontFamily)) continue; st.add(`${c.fontFamily.split(',')[0]} ${c.fontVariantNumeric}`); } return [...st]; })() };
        });
        info[name].meta = m;
        if (!m.title) add(name, w, 'meta', 'no <title>'); if (!m.desc) add(name, w, 'meta', 'no meta description');
        if (!m.ogt || !m.ogd || !m.ogi) add(name, w, 'meta', 'sharing text or image missing (og:title, og:description, og:image)');
        if (!m.lang) add(name, w, 'meta', 'no lang attribute');
        if (m.h1 !== 1) add(name, w, 'heading', `${m.h1} h1 elements (one required)`);
        for (const s of m.skips) add(name, w, 'heading', `heading level skipped ${s}`);
        if (m.inline) add(name, w, 'code', `${m.inline} inline style attribute(s)`);
        if (m.styleTags) add(name, w, 'code', `${m.styleTags} <style> block(s): CSS belongs in site.css`);
        if (m.sheets !== 1) add(name, w, 'code', `${m.sheets} stylesheets (one site.css expected)`);
        if (m.badClass.length) add(name, w, 'code', 'class names not prefixed by component: ' + m.badClass.join(' '));
        if (!m.landmarks) add(name, w, 'code', 'missing header, main or footer landmark');
        if (m.imgs) add(name, w, 'code', `${m.imgs} image(s) without alt, width or height`);
        if (m.lazy) add(name, w, 'weight', `${m.lazy} below-the-fold image(s) not lazy-loaded`);
        for (const x of m.stacked) add(name, w, 'rules', `two rules stacked within 8px: ${x} (one rule per edge)`);
        if (m.figs.length > 1) add(name, w, 'numerals', `figures set in ${m.figs.length} styles: ${m.figs.slice(0, 3).join(' | ')} (one numeral style)`);
      }
      await p.close();
      if (cfg.mode === 'page' && cfg.expansion && (w === 390 || w === 320)) {
        const q = await b.newPage({ viewport: { width: w, height: 900 }, reducedMotion: 'reduce' });
        await q.goto('file://' + file); await q.waitForTimeout(100);
        const e = await q.evaluate(({ w, k }) => {
          const tw = document.createTreeWalker(document.querySelector('main') || document.body, NodeFilter.SHOW_TEXT);
          const ns = []; while (tw.nextNode()) ns.push(tw.currentNode);
          for (const n of ns) { const t = n.data; if (t.trim().length < 2) continue; const extra = Math.round(t.length * (k - 1)); let add = ''; const src = t.replace(/\s+/g, ' ').trim() || 'x'; while (add.length < extra) add += ' ' + src; n.data = t + add.slice(0, extra); }
          const o = { overflow: document.documentElement.scrollWidth > w + 1, clipped: 0 };
          for (const el of document.querySelectorAll('main *')) { const c = getComputedStyle(el); if ((c.overflow === 'hidden' || c.overflowY === 'hidden') && el.scrollHeight > el.clientHeight + 2 && el.textContent.trim()) o.clipped++; }
          return o;
        }, { w, k: cfg.expansion });
        if (e.overflow) add(name, w, 'expansion', `copy x${cfg.expansion} causes horizontal scroll at ${w}px`);
        if (e.clipped) add(name, w, 'expansion', `copy x${cfg.expansion} is clipped in ${e.clipped} element(s) at ${w}px`);
        await q.close();
      }
    }
    if (cfg.mode !== 'rough') {
      const q = await b.newPage({ viewport: { width: cfg.widths[0], height: 900 }, reducedMotion: 'no-preference' });
      await q.goto('file://' + file); await q.waitForTimeout(200);
      const mo = await q.evaluate(() => {
        const long = document.getAnimations().filter(a => { const t = a.effect && a.effect.getTiming(); return t && (t.iterations === Infinity || (t.duration || 0) * (t.iterations || 1) > 5000); });
        const pause = !!document.querySelector('button[aria-label*="ause" i], button[data-pause]');
        return { long: long.length, pause };
      });
      await q.close();
      const r2 = await b.newPage({ viewport: { width: cfg.widths[0], height: 900 }, reducedMotion: 'reduce' });
      await r2.goto('file://' + file); await r2.waitForTimeout(200);
      const moving = await r2.evaluate(() => document.getAnimations().filter(a => a.playState === 'running' && ((a.effect && a.effect.getTiming().duration) || 0) > 10).length);
      await r2.close();
      if (mo.long && !mo.pause) add(name, cfg.widths[0], 'motion', `${mo.long} animation(s) run over 5 seconds with no pause control`);
      if (moving) add(name, cfg.widths[0], 'motion', `${moving} animation(s) still run with reduced motion`);
    }
  }
  await b.close();
  process.stdout.write(JSON.stringify({ findings: out, info }));
})().catch(e => { process.stdout.write(JSON.stringify({ error: String(e) })); process.exit(2); });
