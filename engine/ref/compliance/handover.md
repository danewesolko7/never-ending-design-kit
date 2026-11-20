## 6. Handover (S9)
checkpoint.py runs comply.py --report and puts out/package/compliance/ in the package:
- checklist.md: every jurisdiction and law in force, every requirement with its status, and the manual items still to do (legal review, keyboard and screen-reader tests, real browsers, deployed headers, processing agreements, records of processing, and the rest that apply).
- data-inventory.md: each outside service with purpose, category, when it loads, processor and country; what is stored on the device; each form and its fields; a line for the host's server logs. The client's lawyer starts the records of processing from it.
- acr.md: a WCAG 2.2 conformance report template at the brief's level, with the kit's automated evidence beside each criterion it touches. Every row is confirmed by hand before anyone publishes a conformance claim.
- headers/: the same security headers for Netlify and Cloudflare Pages, nginx, Apache and Vercel.
Packaging blocks while comply.py fails. A pending legal review is a client item: the CD resolves it or ships with --ship-open.
