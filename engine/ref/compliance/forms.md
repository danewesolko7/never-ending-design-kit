## 4. Forms (S7 components, S8 pages)
- Ask only for what the task needs; mark the few optional fields, not the required ones.
- Every field has a visible label; placeholders only show format. autocomplete tokens on personal fields (WCAG 1.3.5).
- A short privacy line inside the form, before the button: what happens to the data, with a link to the privacy page. comply.py fails a form that collects data without it.
- No box ticked in advance. Marketing consent is its own unticked box, separate from the main action.
- Errors: named in text next to the field and summarised at the top, with focus moved there; never colour alone (WCAG 3.3.1 to 3.3.4).
- Anti-spam without a puzzle: a hidden honeypot field and a time check, never an image or audio CAPTCHA (WCAG 1.1.1, and 3.3.8 at sign-in).
- The form posts over https to an endpoint declared in compliance.third_parties (type form), or to the site itself.
- Newsletter: double opt-in, say what will be sent and how often, and an unsubscribe link in every email.
- A confirmation page or message that says what happens next (reach_exempt "thanks").
