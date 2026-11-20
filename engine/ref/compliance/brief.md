## 1. The compliance brief (S0)
Ask in the one question round; leave nothing to assume. Unknowns go to open[] with owner client.
- Markets: the countries and states the site serves, as codes from jurisdictions.json (EU, DE, UK, US, US-CA, CA-QC, BR, ZA, AU, JP ...), or "all". A code brings in its parent (DE brings EU).
- Sector: commercial, public or nonprofit. Public bodies have their own accessibility duties; commercial sites need provider details and a register entry.
- Outside services: every host the site will call (analytics, ads, fonts, maps, video, booking, forms, chat), each with purpose, category (necessary, analytics, marketing, media), types (script, style, img, font, connect, frame, form, media), processor and country. Prefer none: self-host fonts and images.
- Selling or sharing data, or targeted ads (sells_or_shares); online sales (ecommerce); accounts; forms that collect personal data; a newsletter; children in the audience.
- site_url (https), security_contact (an email or https link), lang and, if needed, dir.
- legal_review starts "pending".
Run tools/policy.py after writing brief.json: it prints the pages and features the markets require. Put them in brief.md.
