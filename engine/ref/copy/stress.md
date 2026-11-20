## 2. Worst-case content (S6, S7, S8)
Design for the longest, shortest and strangest real value, not the sample (after Emil Kowalski's break-ui, MIT). pass.py stress adds a 30-letter compound to every heading and a 65-character email to text and links at 320px and fails sideways scroll or cut-off text; pass.py spacing applies the WCAG 1.4.12 text-spacing overrides at 390px. By hand, try in each component:
- Names: long and hyphenated with accents, one letter, right-to-left, no spaces (Chinese, Japanese), an emoji first.
- Unbreakable strings: emails, web addresses, file names, reference numbers.
- Translated labels about 30% longer; numbers at zero, one, a thousand and a million, negative, with the locale's separators.
- Lists with no items, one item and very many; one item far larger than the rest.
- Missing images, very wide or very tall images, slow images (reserve their size).
- Every state at once: loading, empty, error, partial data.
Fixes: text wraps (overflow-wrap: anywhere; min-width: 0 on flex and grid children); heights follow content; truncation only with a way to read the whole; plurals and dates from the language's own rules.
