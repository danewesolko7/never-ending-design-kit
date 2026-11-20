#!/usr/bin/env python3
"""Copy tells: words, stock lines and shapes that make site copy read as machine-written (pass.py copy checks).

    tells.py <page.html> [...]      print the tells found in each built page's main text (pass.py runs it itself)

Hard tells fail (check copy:<id>): a banned stand-in word, a stock line, template or chat residue, process talk.
Soft tells warn (copy-advice:<id>) past their cap: em dashes, exclamation marks, contrast frames, negation runs,
virtue words, two-fragment headings, unsourced proof figures, the default cast of invented names.
A word that is literal for the trade (a climbing harness, bespoke tailoring) goes in brief.json copy_allow[].
Lists distilled from Taste Skill's copy tells (Leonxlnx, MIT) and the kit's own reviews; see NOTICE.
The fix is always a fact from the brief in the word's place, never a synonym.
"""
import os, re, sys
from html.parser import HTMLParser

BAN = ['delve', 'tapestry', 'testament to', 'realm', 'embark', 'beacon', 'multifaceted', 'paradigm', 'myriad', 'plethora',
       'meticulous', 'intricate', 'interplay', 'garner', 'elevate', 'elevates', 'unlock', 'unlocks', 'unleash', 'empower',
       'empowers', 'harness', 'supercharge', 'turbocharge', 'seamless', 'seamlessly', 'effortless', 'effortlessly',
       'cutting-edge', 'revolutionary', 'revolutionise', 'revolutionize', 'transformative', 'holistic', 'next-level',
       'next-generation', 'world-class', 'best-in-class', 'game-changer', 'game-changing', 'state-of-the-art', 'bespoke',
       'synergy', 'synergies', 'leverage', 'reimagine', 'reimagined', 'robust', 'nestled', 'unparalleled', 'unrivalled',
       'unrivaled', 'curated', 'elevated']
STOCK = [r"in today'?s (fast-paced|digital|modern) world", r'unlock the (power|potential) of', r'the future of \w+ is here',
         r'say goodbye to', r"whether you'?re an? .{1,40} or an?", r'join (thousands|millions|hundreds) of',
         r'trusted by (teams|businesses|companies) (worldwide|everywhere|around the world)', r'imagine a world where',
         r'ready to (transform|take|elevate) your', r'look no further', r'one-stop shop', r'at your fingertips',
         r'in just a few clicks', r"it'?s not just an? .{1,30}, it'?s", r'not only .{1,40} but also', r"here'?s the thing",
         r'let that sink in', r'where .{1,25} meets .{1,25}', r'in the heart of', r'take (it|your \w+) to the next level']
RESIDUE = [r'\bcertainly!', r'i hope this helps', r'\[(company|business|client) name\]', r'lorem ipsum', r'\{\{[^}]*\}\}',
           r'\*\*[^*]+\*\*', r'(^|\s)##\s', r'\[NEED\]', r'as an ai\b']
PROCESS = [r'\bthis section (shows|covers|explains)', r"below,? you('?ll| will) find", r'here are \d+ (reasons|ways|things)',
           r"we'?ve added", r'scroll down to']
VIRTUE = ['honest', 'genuinely', 'truly', 'simply', 'thoughtful', 'thoughtfully', 'carefully', 'intentional', 'dependable']
CAST = ['priya', 'okafor', 'elara', 'kestrel', 'halcyon', 'brightloop', 'northwind', 'fieldnote', 'acme', 'nimbus', 'zenith']
PROOF = r'\b\d+(\.\d+)?x (faster|more|better)\b|\b\d{1,3}(,\d{3})+\+? (teams|customers|users|businesses)\b|\b\d{2,3}% (satisfied|happier|faster|of (teams|customers))\b'
CAPS = {'em-dash': 1, 'exclaim': 0, 'contrast': 2, 'negation': 1, 'virtue': 1, 'two-fragment': 1}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.main = self.skip = 0
        self.heads, self.body, self._h = [], [], None

    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.main += 1
        if tag in ('script', 'style'):
            self.skip += 1
        if self.main and re.fullmatch(r'h[1-4]', tag):
            self._h = []

    def handle_endtag(self, tag):
        if tag == 'main' and self.main:
            self.main -= 1
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1
        if re.fullmatch(r'h[1-4]', tag) and self._h is not None:
            self.heads.append(' '.join(self._h).strip()); self._h = None

    def handle_data(self, d):
        if self.main and not self.skip:
            self.body.append(d)
            if self._h is not None:
                self._h.append(d.strip())


def words_re(ws):
    return re.compile(r'(?<![\w-])(' + '|'.join(re.escape(w) for w in ws) + r')(?![\w-])', re.I)


def check(path, allow=()):
    """[(id, hard, detail)] for one built page."""
    t = Text(); t.feed(open(path, encoding='utf-8').read())
    text = re.sub(r'\s+', ' ', ' '.join(t.body)).replace(' ', ' ').strip()
    text = text.replace('’', "'").replace('‘', "'")
    low, out = text.lower(), []
    ban = [w for w in BAN if w not in {a.lower() for a in allow}]
    for m in sorted({m.group(1).lower() for m in words_re(ban).finditer(text)}):
        out.append(('slop-word', True, f'"{m}" stands in for a fact: say the fact'))
    for name, pats, hard, why in (('stock-phrase', STOCK, True, 'a stock line'), ('residue', RESIDUE, True, 'template or chat residue'),
                                  ('process-talk', PROCESS, True, 'the page talks about itself')):
        for p in pats:
            m = re.search(p, low, re.I | re.M)
            if m:
                out.append((name, hard, f'{why}: "{m.group(0).strip()[:50]}"'))
    n = max(1, len(text.split()))
    soft = {'em-dash': (text.count('—') * 100 // n, 'em dashes per 100 words'),
            'exclaim': (len(re.findall(r'!', text)), 'exclamation mark(s) in body copy'),
            'contrast': (len(re.findall(r"\b(isn'?t|is not|not) (just |only |a |about )?\w+[^.]{0,30}\b(but|it'?s)\b|\brather than\b|\binstead of\b|\bwithout the\b", low)), 'contrast frames ("not X but Y" and its substitutes)'),
            'negation': (len(re.findall(r'\bno \w+(,| or) no \w+', low)), 'negation runs ("no X, no Y")'),
            'virtue': (len(words_re(VIRTUE).findall(text)), 'virtue words (show it with a fact)'),
            'two-fragment': (sum(1 for h in t.heads if re.fullmatch(r'[^.]{2,40}\.\s+[^.]{2,40}\.', h)), 'two-fragment headings ("X. Y.")')}
    for k, (v, what) in soft.items():
        if v > CAPS[k]:
            out.append((k, False, f'{v} {what} (cap {CAPS[k]})'))
    m = re.search(PROOF, low)
    if m:
        out.append(('proof-figure', False, f'"{m.group(0)}": a round proof figure needs its source (or [NEW])'))
    cast = sorted({m.group(1).lower() for m in words_re(CAST).finditer(text)})
    if cast:
        out.append(('default-cast', False, f'stock names {", ".join(cast)}: names only from the brief'))
    return out


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    bad = 0
    for f in a:
        for i, hard, d in check(f):
            print(f'{"FAIL" if hard else "warn"} copy {i}: {os.path.basename(f)}: {d}')
            bad += hard
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
