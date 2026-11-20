/* Consent manager (kit primitive). build.py adds it, with the banner, only when brief.json declares a third party
   outside "necessary". Rules it keeps:
   - nothing outside "necessary" loads until the visitor chooses; with no script, nothing loads at all;
   - "Reject all" sits beside "Accept all" with the same look; no box comes ticked;
   - a Global Privacy Control signal keeps "marketing" (sale, sharing, targeted advertising) off;
   - the footer's settings button ([data-consent-open]) reopens the choices at any time.
   Gated items: <script type="text/plain" data-consent="<category>" data-src="https://..." [data-integrity="..."]>,
   or any element (iframe, img) with data-consent and data-src. The choice is stored in localStorage "k-consent"
   with a version and the time; nothing else is stored. Listen for the "k-consent" event to start a gated tool. */
(function () {
  'use strict';
  var KEY = 'k-consent', V = 1, d = document;
  var box = d.getElementById('k-consent');
  if (!box) return;
  var gpc = navigator.globalPrivacyControl === true;
  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };
  var cats = box.querySelectorAll('[data-cat]');
  var field = box.querySelector('[data-consent-cats]');
  var btn = function (a) { return box.querySelector('[data-consent-act="' + a + '"]'); };

  function read() {
    try { var c = JSON.parse(localStorage.getItem(KEY)); return c && c.v === V ? c : null; } catch (e) { return null; }
  }
  function write(c) { try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) { /* private mode: ask again next visit */ } }
  function load(c) {
    each(d.querySelectorAll('[data-consent][data-src]'), function (el) {
      if (!c[el.getAttribute('data-consent')] || el.hasAttribute('data-consent-done')) return;
      el.setAttribute('data-consent-done', '');
      if (el.tagName === 'SCRIPT') {
        var s = d.createElement('script');
        s.src = el.getAttribute('data-src');
        if (el.getAttribute('data-integrity')) { s.integrity = el.getAttribute('data-integrity'); s.crossOrigin = 'anonymous'; }
        el.parentNode.insertBefore(s, el.nextSibling);
      } else {
        el.setAttribute('src', el.getAttribute('data-src'));
      }
    });
  }
  // while the banner is open the page keeps room for it, so nothing focused or read ends up under it (WCAG 2.4.11)
  function room(on) {
    var h = d.documentElement;
    h.classList.toggle('k-consent-on', on);
    if (on) h.style.setProperty('--k-consent-h', box.offsetHeight + 'px'); else h.style.removeProperty('--k-consent-h');
  }
  function choose(c) {
    if (gpc) c.marketing = false;
    c.v = V; c.gpc = gpc; c.time = new Date().toISOString();
    write(c); box.hidden = true; room(false); load(c);
    d.dispatchEvent(new CustomEvent('k-consent', { detail: c }));
  }
  function all(on) {
    var c = {};
    each(cats, function (x) { c[x.getAttribute('data-cat')] = on; });
    return c;
  }
  function open(detail) {
    field.hidden = !detail; btn('save').hidden = !detail;
    btn('choose').setAttribute('aria-expanded', String(detail));
    if (!box.hidden) room(true);
  }
  function show(detail) {
    var c = read() || {};
    each(cats, function (x) {
      var k = x.getAttribute('data-cat');
      x.checked = !!c[k];
      if (gpc && k === 'marketing') { x.checked = false; x.disabled = true; }
    });
    box.hidden = false; open(detail);
    if (typeof ResizeObserver === 'function' && !box._ro) { box._ro = new ResizeObserver(function () { if (!box.hidden) room(true); }); box._ro.observe(box); }
  }

  btn('accept').addEventListener('click', function () { choose(all(true)); });
  btn('reject').addEventListener('click', function () { choose(all(false)); });
  btn('choose').addEventListener('click', function () { open(field.hidden); });
  btn('save').addEventListener('click', function () {
    var c = {};
    each(cats, function (x) { c[x.getAttribute('data-cat')] = x.checked; });
    choose(c);
  });
  each(d.querySelectorAll('[data-consent-open]'), function (b) {
    var wrap = b.closest('[hidden]');
    if (wrap) wrap.hidden = false;
    b.hidden = false;
    b.addEventListener('click', function () {
      show(true);
      var t = box.querySelector('.k-consent-title');
      if (t) { t.setAttribute('tabindex', '-1'); t.focus(); }
    });
  });
  if (gpc) each(box.querySelectorAll('[data-consent-gpc]'), function (p) { p.hidden = false; });
  var saved = read();
  if (saved) load(saved); else show(false);
})();
