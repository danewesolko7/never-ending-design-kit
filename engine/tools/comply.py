#!/usr/bin/env python3
"""Compliance checks: the legal pages, links and behaviour each jurisdiction in the brief asks for.

    comply.py --plan       S2: brief.json compliance{} is filled and content.json plans every required page
    comply.py              the built site (runs build.py --all): required pages and what each must cover, footer
                           links on every page, consent (banner, reject as easy as accept, nothing loads before a
                           choice, GPC), forms, outside hosts against the data inventory, CSP-ready markup,
                           security.txt, canonical, favicon, robots.txt and sitemap.xml
    comply.py --report     the site check, then out/package/compliance/: checklist.md (every requirement and the
                           manual items), data-inventory.md, acr.md (WCAG 2.2 conformance report template) and
                           headers/ (_headers, nginx.conf, apache.htaccess, vercel.json)

Rules: ref/compliance/jurisdictions.json via tools/policy.py. Prints 20 lines or fewer; the full report is
out/reports/comply.md and out/comply.json. Exit 1 on any failure. A check the CD overrode
(gate.py --override comply --target <requirement id or check> --reason "..") is reported as OVERRIDDEN.
What a page must cover is matched in English only; for other languages it is listed for a person to check.
Passing means the pages and patterns exist and work. It is not legal advice: compliance.legal_review stays
"pending" until a lawyer approves the words, and checkpoint.py lists it as a client item until then.
"""
import datetime, glob, json, os, re, subprocess, sys
from html.parser import HTMLParser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, P, Out, current_project, die, event, node_env, read_json, write_atomic, write_json
import policy

S = read_json(J('settings.json'))
SUBRES = {'script': 'src', 'img': 'src', 'iframe': 'src', 'source': 'src', 'video': 'src', 'audio': 'src',
          'embed': 'src', 'object': 'data', 'track': 'src'}


class Scan(HTMLParser):
    """What comply.py needs from one built page."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = {'footer': 0, 'main': 0, 'script': 0, 'a': 0}
        self.footer_links, self.footer_text, self.main_text = [], [], []
        self.forms, self.scripts, self.handlers, self.jsurls, self.insecure, self.external = [], [], [], [], [], []
        self.canonical = self.icon = self.consent = self.consent_open = self.noindex = False
        self._link = None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        if tag in self.depth:
            self.depth[tag] += 1
        for k, v in attrs:
            if k.startswith('on'):
                self.handlers.append(f'{tag} {k}')
            if k in ('href', 'src', 'action', 'formaction', 'data-src') and (v or '').strip().lower().startswith('javascript:'):
                self.jsurls.append(f'{tag} {k}')
        if tag == 'a' and self.depth['footer']:
            self._link = [a.get('href', ''), []]
        if tag == 'a' and self.forms and self.forms[-1].get('open'):
            self.forms[-1]['links'].append(a.get('href', ''))
        if tag == 'form':
            self.forms.append({'open': True, 'fields': [], 'ticked': [], 'links': [], 'action': a.get('action', '')})
            self._url(tag, a.get('action', ''), 'form')
        if self.forms and self.forms[-1].get('open') and tag in ('input', 'select', 'textarea'):
            ty = a.get('type', 'text').lower() if tag == 'input' else tag
            if ty not in ('hidden', 'submit', 'button', 'reset', 'image'):
                self.forms[-1]['fields'].append(a.get('name') or a.get('id') or ty)
            if ty in ('checkbox', 'radio') and 'checked' in a and 'disabled' not in a:
                self.forms[-1]['ticked'].append(a.get('name') or a.get('id') or ty)
        if tag == 'script':
            self.scripts.append({'src': a.get('src', ''), 'type': a.get('type', '').lower(), 'data_src': a.get('data-src', ''),
                                 'integrity': a.get('integrity') or a.get('data-integrity', ''), 'consent': a.get('data-consent', ''), 'text': ''})
        if tag in SUBRES and a.get(SUBRES[tag]):
            self._url(tag, a[SUBRES[tag]], tag, gated=False, integrity=a.get('integrity', ''))
        if a.get('data-src') and a.get('data-consent'):
            self._url(tag, a['data-src'], tag, gated=True, integrity=a.get('data-integrity', ''))
        if tag == 'link':
            rel = a.get('rel', '').lower()
            if 'canonical' in rel:
                self.canonical = a.get('href', '')
            if 'icon' in rel:
                self.icon = True
            if any(r in rel for r in ('stylesheet', 'icon', 'preload', 'manifest', 'modulepreload')):
                self._url(tag, a.get('href', ''), 'style' if 'stylesheet' in rel else 'link', integrity=a.get('integrity', ''))
        if tag == 'meta' and a.get('name', '').lower() == 'robots' and 'noindex' in a.get('content', '').lower():
            self.noindex = True
        if a.get('id') == 'k-consent':
            self.consent = True
        if 'data-consent-open' in a and self.depth['footer']:
            self.consent_open = True

    def _url(self, tag, url, kind, gated=False, integrity=''):
        u = (url or '').strip()
        if u.lower().startswith('http://'):
            self.insecure.append(f'{tag} {u[:80]}')
        m = re.match(r'^(?:https?:)?//([^/:?#]+)', u, re.I)
        if m:
            self.external.append({'tag': tag, 'kind': kind, 'host': m.group(1).lower(), 'url': u, 'gated': gated, 'integrity': bool(integrity)})

    def handle_endtag(self, tag):
        if tag in self.depth and self.depth[tag]:
            self.depth[tag] -= 1
        if tag == 'a' and self._link is not None and not self.depth['a']:
            self.footer_links.append((self._link[0], ' '.join(self._link[1]).strip()))
            self._link = None
        if tag == 'form' and self.forms:
            self.forms[-1]['open'] = False

    def handle_data(self, data):
        if self.depth['script'] and self.scripts:
            self.scripts[-1]['text'] += data
            return
        if self.depth['footer']:
            self.footer_text.append(data)
            if self._link is not None:
                self._link[1].append(data.strip())
        if self.depth['main']:
            self.main_text.append(data)


def scan(path):
    s = Scan()
    s.feed(open(path, encoding='utf-8').read())
    s.footer_text = re.sub(r'\s+', ' ', ' '.join(s.footer_text)).strip()
    s.main_text = re.sub(r'\s+', ' ', ' '.join(s.main_text)).strip()
    return s


def href_page(h):
    m = re.match(r'^(?:\./)?([A-Za-z0-9_-]+)\.html(?:[#?].*)?$', h or '')
    return m.group(1) if m else None


class Report:
    def __init__(self, o):
        self.o, self.status, self.per_page = o, {}, {}
        self.over = {x['target']: x['reason'] for x in read_json(P('overrides.json'), {}).get('comply', [])}

    def page(self, rid, sev, page, msg):
        """A finding on one page; the same finding on several pages prints once, with the pages listed."""
        self.per_page.setdefault((rid, sev, msg), []).append(page)

    def flush(self):
        for (rid, sev, msg), ps in self.per_page.items():
            ps = sorted(set(ps))
            self.add(rid, sev, f'{msg} ({ps[0]})' if len(ps) == 1 else f'{msg} ({len(ps)} pages: {", ".join(ps[:4])}{" ..." if len(ps) > 4 else ""})')
        self.per_page = {}

    def add(self, rid, sev, msg):
        """sev: fail | warn | note. rid: the requirement id (or check name) a CD override can target."""
        if sev == 'fail' and rid in self.over:
            self.o.add(f'OVERRIDDEN {rid}: {msg} (CD: {self.over[rid][:60]})')
            self.status.setdefault(rid, 'overridden')
            return
        label = {'fail': 'FAIL', 'warn': 'warn', 'note': 'note'}[sev]
        self.o.add(f'{label} {rid}: {msg}', sev == 'fail')
        if sev in ('fail', 'warn') and self.status.get(rid) != 'fail':
            self.status[rid] = sev


def check_brief(r, brief, mode):
    c = brief.get('compliance')
    if not isinstance(c, dict):
        r.add('brief', 'fail', 'brief.json has no compliance{} block (S0 asks: markets, sector, tracking, forms, sales)')
        return False
    _, sel, unknown, _, _, _ = policy.active(brief)
    if not sel:
        r.add('brief', 'fail', 'compliance.jurisdictions is empty: name the markets the site serves, or "all"')
    for u in unknown:
        r.add('brief', 'fail', f'unknown jurisdiction "{u}" (codes: ref/compliance/jurisdictions.json)')
    if str(brief.get('wcag', 'AAA')).upper() not in ('AA', 'AAA'):
        r.add('brief', 'fail', 'wcag must be AA or AAA (AA is the floor every listed law accepts)')
    for i, t in enumerate(c.get('third_parties') or []):
        if not isinstance(t, dict) or not t.get('host'):
            r.add('brief', 'fail', f'third_parties[{i}] has no host'); continue
        if t.get('category', 'necessary') not in policy.CATEGORIES:
            r.add('brief', 'fail', f'third_parties {t["host"]}: category must be one of {", ".join(policy.CATEGORIES)}')
        if not t.get('purpose'):
            r.add('brief', 'fail', f'third_parties {t["host"]}: no purpose (the data inventory needs it)')
    if c.get('legal_review', 'pending') not in ('pending', 'done'):
        r.add('brief', 'fail', 'compliance.legal_review is "pending" or "done"')
    sev = 'fail' if mode == 'site' else 'warn'
    url = policy.site_url(brief)
    if not url:
        r.add('feature:discover', sev, 'no site_url in brief.json (canonical links, sitemap.xml, robots.txt and security.txt need it)')
    elif not url.startswith('https://'):
        r.add('feature:security', sev, f'site_url {url} is not https')
    if not str(c.get('security_contact') or '').strip():
        r.add('feature:security', sev, 'no compliance.security_contact (security.txt needs an email or https link)')
    return True


def plan(r, brief):
    content = read_json(P('content.json'), {})
    ids = {p.get('id') for p in content.get('pages', [])}
    if not ids:
        r.add('plan', 'fail', 'content.json has no pages yet')
        return
    for role, pid, sev, why in policy.required_pages(brief):
        if pid not in ids:
            r.add(f'page:{role}', sev, f'content.json has no "{pid}" page ({why})')


def site(r, brief):
    sitedir = P('out', 'site')
    files = sorted(glob.glob(os.path.join(sitedir, '*.html')))
    if not files:
        die('comply: no built pages in out/site/ (build.py --all)')
    pages = {os.path.basename(f)[:-5]: scan(f) for f in files}
    R, sel, _, fl, reqs, _ = policy.active(brief)
    en = str(brief.get('lang') or 'en').lower().startswith('en')
    req_pages = policy.required_pages(brief)
    # pages and what they cover
    for role, pid, sev, why in req_pages:
        if pid not in pages:
            r.add(f'page:{role}', sev, f'no {pid}.html ({why})')
    hand = []
    for q in (x for x in reqs if x['kind'] == 'cover'):
        pid = policy.page_id(brief, q['page'])
        if pid not in pages:
            continue
        if not en:
            hand.append(f'{pid}: {q["topic"]}'); continue
        if not re.search(q['pattern'], pages[pid].main_text, re.I):
            r.add(q['id'], 'fail', f'{pid} does not cover {q["topic"]}')
    if hand:
        r.add('cover', 'note', f'{len(hand)} topic(s) to check by hand (not English): ' + '; '.join(hand[:3]) + (' ...' if len(hand) > 3 else ''))
    feats = {x['feature'] for x in reqs if x['kind'] == 'feature'}
    exempt = set(S.get('reach_exempt') or [])
    # footer: every required page linked from every page's footer
    need = [(role, pid) for role, pid, sev, _ in req_pages if sev == 'fail' and R['pages'].get(role, {}).get('footer') and pid in pages]
    for name, s in pages.items():
        linked = {href_page(h) for h, _ in s.footer_links}
        miss = [pid for _, pid in need if pid not in linked]
        if miss and 'footer' in feats:
            r.page('feature:footer', 'fail', name, f'footer has no link to {", ".join(miss)} (chrome partial footer.html places {{{{legal}}}})')
        if 'choices-link' in feats:
            if not any(re.search(r'do not sell or share|your privacy choices', t, re.I) for _, t in s.footer_links):
                r.page('feature:choices-link', 'fail', name, f'the footer link must read "Do Not Sell or Share My Personal Information" or "Your Privacy Choices"')
        if 'vat-footer' in feats and not re.search(r'P\.?\s?IVA|Partita IVA|\bVAT\b', s.footer_text, re.I):
            r.page('feature:vat-footer', 'fail', name, f'no VAT number (Partita IVA) in the footer')
        if 'a11y-footer' in feats and not re.search(r'accessibilit\S*\s*:?\s*(non|partiellement|totalement)?\s*conforme', s.footer_text, re.I):
            r.page('feature:a11y-footer', 'fail', name, f'no accessibility compliance status in the footer (RGAA)')
        if 'consent' in feats:
            if not s.consent:
                r.page('feature:consent', 'fail', name, f'no consent banner')
            if not s.consent_open:
                r.page('feature:consent', 'fail', name, f'no cookie-settings button in the footer ({{{{legal}}}} places it)')
    # forms
    pp = policy.page_id(brief, 'privacy')
    for name, s in pages.items():
        for i, f in enumerate(s.forms):
            if f['fields'] and not any(href_page(h) == pp for h in f['links']):
                r.page('feature:forms', 'fail', name, f'form {i + 1} collects {", ".join(f["fields"][:4])} with no link to {pp}.html inside it')
            for t in f['ticked']:
                r.page('feature:forms', 'fail', name, f'form {i + 1} has "{t}" ticked before the visitor chooses')
            if f['fields'] and not fl['forms']:
                r.page('brief', 'warn', name, f'a form collects data but compliance.forms_personal_data is false')
    # outside hosts (static): declared, gated when not necessary, integrity on scripts and styles
    tp = {str(t['host']).lower().replace('https://', '').replace('http://', '').rstrip('/'): t for t in policy.third_parties(brief)}
    for name, s in pages.items():
        for x in s.external:
            t = tp.get(x['host'])
            if not t:
                r.page('feature:hosts', 'fail', name, f'{x["host"]} ({x["tag"]}) is not declared in compliance.third_parties')
                continue
            if t.get('category', 'necessary') != 'necessary' and not x['gated']:
                r.page('feature:hosts', 'fail', name, f'{x["host"]} ({t.get("category")}) loads without waiting for consent: use data-consent and data-src')
            if x['kind'] in ('script', 'style') and not x['integrity']:
                r.page('feature:security', 'warn', name, f'{x["host"]} {x["kind"]} has no integrity hash (SRI)')
    # security: CSP-ready markup
    for name, s in pages.items():
        inline = [x for x in s.scripts if not x['src'] and x['text'].strip() and x['type'] not in ('application/ld+json',)]
        if inline:
            r.page('feature:security', 'fail', name, f'{len(inline)} inline script(s): scripts are files, so the Content Security Policy can forbid inline code')
        if s.handlers:
            r.page('feature:security', 'fail', name, f'inline event handler(s): {", ".join(s.handlers[:3])}')
        if s.jsurls:
            r.page('feature:security', 'fail', name, f'javascript: URL(s): {", ".join(s.jsurls[:3])}')
        if s.insecure:
            r.page('feature:security', 'fail', name, f'insecure http:// resource(s): {", ".join(s.insecure[:2])}')
    sec = os.path.join(sitedir, '.well-known', 'security.txt')
    if not os.path.exists(sec):
        r.add('feature:security', 'fail', 'no .well-known/security.txt (compliance.security_contact)')
    else:
        t = open(sec, encoding='utf-8').read()
        m = re.search(r'^Expires:\s*(\S+)', t, re.M)
        if not re.search(r'^Contact:\s*\S+', t, re.M) or not m:
            r.add('feature:security', 'fail', 'security.txt needs Contact and Expires (RFC 9116)')
        elif m.group(1)[:10] <= datetime.date.today().isoformat():
            r.add('feature:security', 'fail', 'security.txt has expired: rebuild')
    if not os.path.exists(os.path.join(sitedir, '_headers')):
        r.add('feature:security', 'fail', 'no _headers (build.py --all writes the security headers)')
    # discoverability
    url = policy.site_url(brief)
    for name, s in pages.items():
        if url and name not in exempt and name != 'specimen' and not s.canonical:
            r.page('feature:discover', 'fail', name, f'no canonical link')
        if not s.icon:
            r.page('feature:discover', 'fail', name, f'no favicon (add images/favicon.svg, .png or .ico)')
    if url:
        for f in ('robots.txt', 'sitemap.xml'):
            if not os.path.exists(os.path.join(sitedir, f)):
                r.add('feature:discover', 'fail', f'no {f}')
        sm = open(os.path.join(sitedir, 'sitemap.xml'), encoding='utf-8').read() if os.path.exists(os.path.join(sitedir, 'sitemap.xml')) else ''
        for name in pages:
            if name not in exempt and name != 'specimen' and f'/{name}.html<' not in sm:
                r.add('feature:discover', 'fail', f'sitemap.xml does not list {name}')
    # behaviour in a browser: requests and consent
    nec = [h for h, t in tp.items() if t.get('category', 'necessary') == 'necessary']
    cfg = {'files': [os.path.abspath(f) for f in files if not f.endswith('specimen.html')],
           'consent': 'consent' in feats, 'gpc': 'consent' in feats and ('gpc' in feats or fl['marketing']),
           'necessary': nec, 'declared': list(tp)}
    p = subprocess.run(['node', J('tools', 'comply.js'), json.dumps(cfg)], capture_output=True, text=True, env=node_env())
    try:
        d = json.loads(p.stdout)
    except ValueError:
        die('comply: browser probe failed: ' + (p.stderr or p.stdout)[-400:])
    if 'error' in d:
        die('comply: browser probe failed: ' + d['error'][:300])
    event('render', len(cfg['files']) * (3 if cfg['consent'] else 1))
    rid = {'undeclared': 'feature:hosts', 'early': 'feature:hosts', 'gpc': 'feature:gpc'}
    seen = set()
    for f in d['findings']:
        key = (f['check'], f['detail'])
        if key in seen:
            continue
        seen.add(key)
        r.page(rid.get(f['check'], 'feature:consent'), 'fail', f['page'], f['detail'])
    r.flush()
    return pages


# ---------- handover ----------
def report(brief, r, pages):
    out = P('out', 'package', 'compliance')
    os.makedirs(os.path.join(out, 'headers'), exist_ok=True)
    R, sel, _, fl, reqs, manual = policy.active(brief)
    c = brief.get('compliance') or {}
    js = R['jurisdictions']
    name = brief.get('site_name') or current_project()
    st = lambda rid: {'fail': 'FAIL', 'warn': 'WARN', 'overridden': 'OVERRIDDEN (CD)'}.get(r.status.get(rid), 'PASS')
    L = [f'# {name}: compliance checklist', '',
         f'Built {datetime.date.today().isoformat()} by comply.py. The kit checks that the pages, links and behaviour each law asks for exist and work.',
         'It is not legal advice. Legal review: **' + str(c.get('legal_review', 'pending')) + '**.', '',
         '## Jurisdictions and laws', '']
    for code in sorted(sel, key=lambda x: list(js).index(x)):
        L.append(f'- **{js[code]["name"]}** ({code}; tracking consent model: {js[code].get("consent", "notice")}): ' + '; '.join(js[code]['laws']))
    L += ['', '## Project flags', '', ', '.join(k for k, v in fl.items() if v) or 'none', '', '## Requirements', '',
          '| Status | Requirement | Why or what |', '|---|---|---|']
    done = set()
    for q in reqs:
        key = f'page:{q["page"]}' if q['kind'] == 'page' else q['id']
        if key in done:
            continue
        done.add(key)
        what = q.get('why') if q['kind'] != 'cover' else f'{policy.page_id(brief, q["page"])} covers {q["topic"]}'
        s = 'RECOMMENDED, missing' if r.status.get(key) == 'warn' else st(key)
        L.append(f'| {s} | {key} | {what} |')
    reviewed = str(c.get('legal_review', 'pending')) == 'done'
    L += ['', '## Still to do by hand', ''] + [f'- [{"x" if reviewed and m.startswith("A lawyer") else " "}] {m}' for m in manual] + ['']
    write_atomic(os.path.join(out, 'checklist.md'), '\n'.join(L))
    # data inventory
    D = [f'# {name}: data inventory', '', 'For the records of processing and the privacy and cookie pages. Fill the blanks with the client.', '',
         '## Outside services', '', '| Host | Purpose | Category | Loads | Processor | Country | Privacy link |', '|---|---|---|---|---|---|---|']
    for t in policy.third_parties(brief):
        cat = t.get('category', 'necessary')
        D.append(f'| {t["host"]} | {t.get("purpose", "")} | {cat} | {"always" if cat == "necessary" else "after consent"} | '
                 f'{t.get("processor", "")} | {t.get("country", "")} | {t.get("privacy_url", "")} |')
    if not policy.third_parties(brief):
        D.append('| none | | | | | | |')
    D += ['', '## Stored on the visitor\'s device', '']
    D += (['| Key | Where | Holds | Lasts |', '|---|---|---|---|',
           '| k-consent | localStorage | the consent choice per category, a version, the time, whether GPC was on | until the visitor clears it or chooses again |']
          if policy.consent_on(brief) else ['Nothing: the site sets no cookies and stores nothing.'])
    D += ['', '## Forms', '']
    fr = [(n, i, f) for n, s in (pages or {}).items() for i, f in enumerate(s.forms) if f['fields']]
    D += ([f'- {n} form {i + 1}: {", ".join(f["fields"])} -> {f["action"] or "(no action set)"}' for n, i, f in fr] or ['No form collects data.'])
    D += ['', '## Server', '', '- Hosting provider and its server logs (IP address, time, page): name the provider, the log retention and the legal basis.', '']
    write_atomic(os.path.join(out, 'data-inventory.md'), '\n'.join(D))
    # ACR template
    target = str(brief.get('wcag', 'AAA')).upper()
    levels = ('A', 'AA') if target == 'AA' else ('A', 'AA', 'AAA')
    crit = read_json(J('ref', 'compliance', 'wcag22.json'))['criteria']
    pj = read_json(P('out', 'pass.json'), {})
    auto = 'Automated check passed (confirm by hand)' if pj.get('pass') and pj.get('mode') in ('package', 'page') else 'Automated check not passed yet (run pass.py --package)'
    A = [f'# {name}: accessibility conformance report (template)', '',
         f'Standard: WCAG 2.2, target level {target}. Format follows the ITI VPAT sections; fill it after manual testing.',
         'Status values: Supports, Partially supports, Does not support, Not applicable. "Automated check passed" is evidence, not a verdict.', '',
         '| Criterion | Level | Status | Evidence | Remarks |', '|---|---|---|---|---|']
    for sc, title, lvl, kit in crit:
        if lvl in levels:
            A.append(f'| {sc} {title} | {lvl} | {auto if kit else "Not evaluated"} | {kit} | |')
    A += ['', '## Testing still to do', '', '- Keyboard only, every page and the consent banner', '- VoiceOver (macOS, iOS) and NVDA (Windows)',
          '- 200% and 400% zoom; text spacing bookmarklet (1.4.12)', '- Real users, including disabled people', '']
    write_atomic(os.path.join(out, 'acr.md'), '\n'.join(A))
    for fn, text in policy.header_files(brief).items():
        write_atomic(os.path.join(out, 'headers', fn), text)
    write_atomic(os.path.join(out, 'headers', 'README.md'),
                 '# Server headers\n\nOne set of security headers in four host formats. Netlify and Cloudflare Pages read `_headers` (already in the built site).'
                 ' nginx: paste `nginx.conf` into the server block. Apache: `apache.htaccess` as `.htaccess`. Vercel: merge `vercel.json`.'
                 ' Hosts that cannot set headers (GitHub Pages) cannot send these: choose a host that can, or put a CDN in front.\n')
    return out


def main(a):
    if a and a[0] in ('-h', '--help'):
        print(__doc__); return 0
    current_project()
    event('call')
    mode = 'plan' if '--plan' in a else 'site'
    o = Out('comply', P('out', 'reports', 'comply.md'))
    r = Report(o)
    brief = read_json(P('brief.json'), {})
    pages = None
    if check_brief(r, brief, mode):
        if mode == 'plan':
            plan(r, brief)
        else:
            b = subprocess.run([sys.executable, J('tools', 'build.py'), '--all'], capture_output=True, text=True,
                               env={**os.environ, 'KIT_PROJECT': current_project()})
            if b.returncode:
                print((b.stdout + b.stderr).strip()[-600:]); return 1
            pages = site(r, brief)
    if '--report' in a and mode == 'site':
        out = report(brief, r, pages)
        o.add(f'handover: {os.path.relpath(out, P())}/ (checklist, data inventory, ACR template, headers)')
    _, sel, _, _, reqs, manual = policy.active(brief)
    write_json(P('out', 'comply.json'), {'mode': mode, 'pass': not o.fail, 'status': r.status,
                                          'jurisdictions': sorted(sel), 'manual': manual,
                                          'legal_review': (brief.get('compliance') or {}).get('legal_review', 'pending')})
    fails = sum(1 for v in r.status.values() if v == 'fail')
    return o.done(f'comply {mode}: ' + ('PASS' if not o.fail else 'FAIL') + f' ({len(sel)} jurisdiction(s), {len(reqs)} requirement(s)'
                  + (f', {fails} failing' if fails else '') + ')')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
