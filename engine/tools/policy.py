#!/usr/bin/env python3
"""Compliance rules for one project: which pages, links and features it needs, and its server headers.

    policy.py                  print the project's jurisdictions, flags, required pages and features

Reads brief.json compliance{} and ref/compliance/jurisdictions.json. Shared by build.py (legal footer, consent banner,
robots.txt, sitemap.xml, security.txt, _headers) and comply.py (the checks and the handover). Holds no project value.
The kit makes sure the pages and patterns exist and work; it is not legal advice.
"""
import datetime, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kitlib import J, P, current_project, read_json

CATEGORIES = ('necessary', 'analytics', 'marketing', 'media')
SRC_TYPES = ('script', 'style', 'img', 'font', 'connect', 'frame', 'form', 'media')
RTL = {'ar', 'he', 'fa', 'ur', 'yi', 'ps', 'ckb', 'dv', 'sd', 'ug'}


def rules():
    return read_json(J('ref', 'compliance', 'jurisdictions.json'))


def comp(brief):
    return brief.get('compliance') or {}


def selected(brief, R=None):
    """(codes in force, including parents; unknown codes). 'all' selects every jurisdiction."""
    R = R or rules()
    js = R['jurisdictions']
    want = [str(x) for x in comp(brief).get('jurisdictions') or []]
    if any(x.lower() == 'all' for x in want):
        want = list(js)
    out, unknown = set(), []
    for x in want:
        if x not in js:
            unknown.append(x)
            continue
        while x:
            out.add(x)
            x = js[x].get('parent')
    return out, unknown


def third_parties(brief):
    return [t for t in comp(brief).get('third_parties') or [] if isinstance(t, dict) and t.get('host')]


def flags(brief):
    c = comp(brief)
    cats = {t.get('category', 'necessary') for t in third_parties(brief)}
    sector = str(c.get('sector') or 'commercial').lower()
    return {'tracking': bool(cats - {'necessary'}), 'marketing': 'marketing' in cats or bool(c.get('sells_or_shares')),
            'ecommerce': bool(c.get('ecommerce')), 'accounts': bool(c.get('accounts')),
            'forms': bool(c.get('forms_personal_data')), 'newsletter': bool(c.get('newsletter')),
            'children': bool(c.get('children')), 'public': sector == 'public', 'commercial': sector == 'commercial'}


def applies(when, sel, fl):
    if when.get('in') and not sel & set(when['in']):
        return False
    return all(fl.get(f) for f in when.get('flags', [])) and not any(fl.get(f) for f in when.get('not', []))


def active(brief):
    """(rules, codes, unknown codes, flags, requirements in force, manual items in force)"""
    R = rules()
    sel, unknown = selected(brief, R)
    fl = flags(brief)
    reqs = [r for r in R['requirements'] if applies(r.get('when') or {}, sel, fl)]
    manual = [m['item'] for m in R.get('manual', []) if applies(m.get('when') or {}, sel, fl)]
    return R, sel, unknown, fl, reqs, manual


def page_id(brief, role):
    """A project may rename a legal page: compliance.pages {"privacy": "datenschutz"}."""
    return (comp(brief).get('pages') or {}).get(role, role)


def required_pages(brief):
    """[(role, page id, 'fail' | 'warn', why)], one per role; a failing requirement outranks a recommendation."""
    _, _, _, _, reqs, _ = active(brief)
    out = {}
    for r in reqs:
        if r['kind'] != 'page':
            continue
        if r['page'] not in out or r['severity'] == 'fail':
            out[r['page']] = (r['page'], page_id(brief, r['page']), r['severity'], r.get('why', ''))
    order = list(rules()['pages'])
    return sorted(out.values(), key=lambda x: order.index(x[0]) if x[0] in order else 99)


def legal_roles():
    return [k for k, v in rules()['pages'].items() if v.get('footer')]


def legal_ids(brief):
    """Page ids that belong in the footer's legal list, in the kit's order."""
    return [page_id(brief, r) for r in legal_roles()]


def consent_on(brief):
    return flags(brief)['tracking']


def site_url(brief):
    return str(brief.get('site_url') or comp(brief).get('site_url') or '').rstrip('/')


def text_dir(brief):
    d = str(brief.get('dir') or '').lower()
    if d in ('rtl', 'ltr'):
        return d
    return 'rtl' if str(brief.get('lang') or 'en').split('-')[0].lower() in RTL else 'ltr'


# ---------- headers ----------
def _origin(host):
    h = str(host).strip().rstrip('/')
    return h if re.match(r'^https?://', h) else 'https://' + h


def csp(brief):
    src = {k: ["'self'"] for k in SRC_TYPES}
    src['img'].append('data:')
    src['frame'] = []
    for t in third_parties(brief):
        for ty in t.get('types') or ['script']:
            if ty in src and _origin(t['host']) not in src[ty]:
                src[ty].append(_origin(t['host']))
    return '; '.join([
        "default-src 'self'", 'script-src ' + ' '.join(src['script']), 'style-src ' + ' '.join(src['style']),
        'img-src ' + ' '.join(src['img']), 'font-src ' + ' '.join(src['font']), 'connect-src ' + ' '.join(src['connect']),
        'media-src ' + ' '.join(src['media']), 'frame-src ' + (' '.join(src['frame']) or "'none'"), "object-src 'none'",
        "base-uri 'self'", 'form-action ' + ' '.join(src['form']), "frame-ancestors 'none'", 'upgrade-insecure-requests'])


def headers(brief):
    pay = 'payment=(self)' if flags(brief)['ecommerce'] else 'payment=()'
    return [('Content-Security-Policy', csp(brief)),
            ('Strict-Transport-Security', 'max-age=63072000; includeSubDomains'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Referrer-Policy', 'strict-origin-when-cross-origin'),
            ('Permissions-Policy', f'camera=(), microphone=(), geolocation=(), usb=(), browsing-topics=(), {pay}'),
            ('Cross-Origin-Opener-Policy', 'same-origin'),
            ('X-Frame-Options', 'DENY')]


def header_files(brief):
    """{filename: text} for the hosts the handover covers. Netlify and Cloudflare Pages read _headers from the site."""
    hs = headers(brief)
    q = lambda v: v.replace('"', '\\"')
    return {
        '_headers': '/*\n' + ''.join(f'  {k}: {v}\n' for k, v in hs),
        'nginx.conf': '# inside the server block\n' + ''.join(f'add_header {k} "{q(v)}" always;\n' for k, v in hs)
                      + 'error_page 404 /404.html;\n',
        'apache.htaccess': '<IfModule mod_headers.c>\n' + ''.join(f'  Header always set {k} "{q(v)}"\n' for k, v in hs)
                           + '</IfModule>\nErrorDocument 404 /404.html\n',
        'vercel.json': json.dumps({'headers': [{'source': '/(.*)', 'headers': [{'key': k, 'value': v} for k, v in hs]}]}, indent=1) + '\n',
    }


def security_txt(brief, today=None):
    c = comp(brief)
    contact = str(c.get('security_contact') or '').strip()
    if not contact:
        return None
    if '@' in contact and not contact.startswith(('mailto:', 'https://')):
        contact = 'mailto:' + contact
    exp = (today or datetime.date.today()) + datetime.timedelta(days=364)
    lines = [f'Contact: {contact}', f'Expires: {exp.isoformat()}T00:00:00Z',
             f'Preferred-Languages: {str(brief.get("lang") or "en").split("-")[0]}']
    if site_url(brief):
        lines.append(f'Canonical: {site_url(brief)}/.well-known/security.txt')
    return '\n'.join(lines) + '\n'


def main(a):
    if a and a[0] in ('-h', '--help'):
        print(__doc__); return 0
    current_project()
    brief = read_json(P('brief.json'), {})
    R, sel, unknown, fl, reqs, manual = active(brief)
    print('jurisdictions: ' + (', '.join(sorted(sel)) or 'none (brief.json compliance.jurisdictions is empty)'))
    if unknown:
        print('unknown codes: ' + ', '.join(unknown) + ' (see ref/compliance/jurisdictions.json)')
    print('flags: ' + (', '.join(k for k, v in fl.items() if v) or 'none'))
    print('pages: ' + ', '.join(f'{pid}{"" if sev == "fail" else " (recommended)"}' for _, pid, sev, _ in required_pages(brief)))
    print('features: ' + ', '.join(r['feature'] for r in reqs if r['kind'] == 'feature'))
    print(f'cover topics: {sum(1 for r in reqs if r["kind"] == "cover")} | manual items: {len(manual)}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
