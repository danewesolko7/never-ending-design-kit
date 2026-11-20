// Browser probe for comply.py: what each built page asks of other hosts, and how the consent banner behaves.
//   node tools/comply.js '<json config>'
// config: {files:[abs paths], consent:bool, gpc:bool, necessary:[hosts], declared:[hosts]}
// Every request off the page's own files is recorded and aborted (nothing leaves the machine).
// Findings: {page, check, detail}. Checks: undeclared (a host not in the brief's third_parties), early (a host outside
// "necessary" asked for before any choice), banner (missing, or not shown on a first visit), equal (reject and accept
// differ in look), ticked (a box ticked before a choice), reject (something outside "necessary" loads after reject, or
// the banner stays), reopen (no working settings button in the footer), gpc (marketing on under a GPC signal).
const { chromium } = require('playwright'); const path = require('path');
const cfg = JSON.parse(process.argv[2] || '{}');
const host = u => { try { return new URL(u).host.toLowerCase(); } catch (e) { return ''; } };
const strip = h => String(h).toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '');
const declared = new Set((cfg.declared || []).map(strip)); const necessary = new Set((cfg.necessary || []).map(strip));
(async () => {
  const b = await chromium.launch(); const out = [];
  const add = (page, check, detail) => out.push({ page, check, detail: String(detail).slice(0, 200) });
  async function visit(file, opts) {
    const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
    if (opts && opts.gpc) await ctx.addInitScript(() => Object.defineProperty(Navigator.prototype, 'globalPrivacyControl', { get: () => true }));
    const reqs = [];
    await ctx.route('**/*', r => { const u = r.request().url(); if (/^(file|data|blob|about):/.test(u)) return r.continue(); reqs.push(u); return r.abort(); });
    const p = await ctx.newPage();
    await p.goto('file://' + file); await p.waitForTimeout(250);
    return { ctx, p, reqs };
  }
  for (const file of cfg.files) {
    const name = path.basename(file, '.html');
    const { ctx, p, reqs } = await visit(file);
    const seen = new Set();
    for (const u of reqs) { const h = host(u); if (!h || seen.has(h)) continue; seen.add(h);
      if (!declared.has(h)) add(name, 'undeclared', `${h} is asked for but not declared in brief.json compliance.third_parties`);
      else if (!necessary.has(h)) add(name, 'early', `${h} loads before any consent choice`); }
    if (cfg.consent) {
      const s = await p.evaluate(() => {
        const box = document.getElementById('k-consent'); if (!box) return { box: false };
        const rj = box.querySelector('[data-consent-act="reject"]'), ac = box.querySelector('[data-consent-act="accept"]');
        const look = el => { if (!el) return null; const c = getComputedStyle(el); const r = el.getBoundingClientRect();
          return { cls: el.className, h: Math.round(r.height), w: Math.round(r.width), fs: c.fontSize, fw: c.fontWeight, bg: c.backgroundColor, fg: c.color, bd: c.borderTopWidth + ' ' + c.borderTopStyle }; };
        return { box: true, shown: !box.hidden && box.getBoundingClientRect().height > 0, reject: look(rj), accept: look(ac),
          ticked: [...box.querySelectorAll('input[type=checkbox]')].filter(i => i.checked && !i.disabled).map(i => i.id) };
      });
      if (!s.box) add(name, 'banner', 'no consent banner (#k-consent): build.py adds it when the brief declares tracking');
      else {
        if (!s.shown) add(name, 'banner', 'the banner is not shown on a first visit');
        if (!s.reject || !s.accept) add(name, 'equal', 'the first layer needs both "reject" and "accept" buttons');
        else { const d = ['cls', 'h', 'fs', 'fw', 'bg', 'fg', 'bd'].filter(k => s.reject[k] !== s.accept[k]);
          if (d.length || Math.abs(s.reject.w - s.accept.w) > s.accept.w * 0.25) add(name, 'equal', `reject and accept differ in ${d.join(', ') || 'width'}`); }
        for (const id of s.ticked) add(name, 'ticked', `${id} is ticked before any choice`);
        if (s.reject) {
          const n0 = reqs.length;
          await p.click('[data-consent-act="reject"]'); await p.waitForTimeout(250);
          const after = reqs.slice(n0).map(host).filter(h => !necessary.has(h));
          if (after.length) add(name, 'reject', `after "reject": ${[...new Set(after)].join(', ')} still load`);
          if (await p.evaluate(() => !document.getElementById('k-consent').hidden)) add(name, 'reject', 'the banner stays after "reject"');
          await p.reload(); await p.waitForTimeout(200);
          if (await p.evaluate(() => !document.getElementById('k-consent').hidden)) add(name, 'reject', 'the choice is not remembered on the next page view');
          const open = await p.$('footer [data-consent-open]');
          if (!open || !(await open.isVisible())) add(name, 'reopen', 'no visible cookie-settings button in the footer');
          else { await open.click(); await p.waitForTimeout(100);
            if (await p.evaluate(() => document.getElementById('k-consent').hidden)) add(name, 'reopen', 'the settings button does not reopen the choices'); }
        }
      }
    }
    await ctx.close();
    if (cfg.consent && cfg.gpc) {
      const g = await visit(file, { gpc: true });
      if (await g.p.$('[data-consent-act="accept"]')) {
        await g.p.click('[data-consent-act="accept"]'); await g.p.waitForTimeout(250);
        const st = await g.p.evaluate(() => { try { return JSON.parse(localStorage.getItem('k-consent')) || {}; } catch (e) { return {}; } });
        if (st.marketing) add(name, 'gpc', 'with a Global Privacy Control signal, "accept" still turns marketing on');
      }
      await g.ctx.close();
    }
  }
  await b.close();
  process.stdout.write(JSON.stringify({ findings: out }));
})().catch(e => { process.stdout.write(JSON.stringify({ error: String(e) })); process.exit(2); });
