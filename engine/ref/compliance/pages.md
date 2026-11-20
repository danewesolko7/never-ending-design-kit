## 2. Legal pages (S2 plans them, S5 writes them)
Page ids are fixed (privacy, cookies, privacy-choices, terms, accessibility, imprint, returns, shipping, paia-manual, 404); compliance.pages renames one. build.py takes them out of the main nav and lists them in the footer of every page. Form: a plain document, one column, headings a reader can scan, the brief's reading level, no legal filler. comply.py checks the topics below in English; other languages are checked by hand.
- privacy: who runs the site and is responsible; what is collected and why; legal basis (EU, UK, CH, BR, TR, ZA); how long it is kept; who receives it and transfers abroad; the visitor's rights and how to use them; the right to complain to the regulator; a named officer where required (BR, SG, Quebec, KR, IN, ZA, CN, TH, PH, ID, VN); California: categories, sale or sharing, no discrimination, GPC and Do Not Track; children if they are in the audience; last updated date.
- cookies: each tool, its purpose, how long it lasts, and how to change the choice (the footer's cookie settings).
- privacy-choices: opting out of sale, sharing and targeted ads; that GPC is honoured. Footer label "Your Privacy Choices" or "Do Not Sell or Share My Personal Information".
- accessibility: the standard (WCAG 2.2 and the level), how far the site meets it, what is not yet accessible, how to report a problem or ask for another format, when it was prepared, and the enforcement procedure for EU and UK public bodies. Write it from out/package/accessibility.md, never claiming more than was tested.
- imprint: name, postal address, email and phone, register and VAT number (commercial), the person responsible for content.
- terms; returns (the 14-day right to cancel in the EU and UK); shipping: when selling.
- paia-manual: South Africa.
- 404: the header and footer, one plain sentence, links on. Not indexed.
