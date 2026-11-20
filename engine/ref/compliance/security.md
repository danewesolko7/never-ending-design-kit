## 5. Security and discoverability (S7, S8, S9)
- Markup works under a strict Content Security Policy: scripts are files, never inline code, event handler attributes or javascript: links (JSON-LD data is allowed). comply.py fails each.
- Everything over https; an outside script or stylesheet carries an integrity hash where its file is fixed.
- build.py --all writes into the site: _headers (Content-Security-Policy built from the declared hosts, HSTS, nosniff, referrer policy, permissions policy, opener policy, frame denial), .well-known/security.txt (RFC 9116, from compliance.security_contact, expiring in a year), robots.txt and sitemap.xml (from site_url).
- Every page has a canonical link, a favicon (images/favicon.svg, .png or .ico from the CD) and a referrer policy; exempt pages (404, thanks, specimen) are not indexed.
- Choose a host that sends headers (Netlify, Cloudflare Pages, Vercel, nginx, Apache); comply.py --report writes the same headers for each. A host that cannot send headers cannot meet this standard.
- Right-to-left languages: build.py sets dir from lang. Write partial CSS with logical properties (margin-inline-start, inset-inline-end, padding-block) so a mirrored site needs no new CSS.
- pass.py measures layout shift and largest paint from local files; field data after launch confirms them.
