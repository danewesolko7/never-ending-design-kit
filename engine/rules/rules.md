# Rules (hard design rules)

The kit is the single source. Read in every session after P0. Precedence: CD > rules-local.md > this file > taste-checks.md > the stage prompt > ref sections.

## Layout
- No table-style layouts on content: no side-by-side text columns, split heroes, label/value rows, spine or gutter columns, sidebars, margin notes, key-value lead-ins ("Measures:", "Source:"), definition grids or card grids. Text reads in one sequence. The page form may vary (stacked chapters, an index or atlas, a reel, a single large diagram, a document).
- Large display numbers in a left column do not work.
- Text never overlaps a photo or crosses the edge between two sections. Overlaps are for shapes, sheets and squares only; if a design overlaps a photo, it does it the same way on every page.
- One loud move per screen, a rest after each loud screen, at most four shared left edges per desktop screen, no near misses.
- Rule hierarchy: one heavy rule, for section dividers only; 1px hairlines inside a section; never two rules stacked; no closing rule under a list.
- A repeated marker (tab, number, label) never floats alone: it sits on a rule or edge, shows its order and keeps one width and treatment.
- Link lists use at most two treatments (short link; title plus description), the arrow pinned to the first line. Sources are a numbered list of plain links.

## Conversion
- Conversion beats concept: a novel move never carries navigation or the main action. Labelled nav, the main action and tap-to-call sit in every header.
- Every page is reachable from the key page by nav, footer site map, hub page or crumbs (pass.py reach).
- The key page shows a short selection of references (about six); the full list has its own page. References are "past" until the owner confirms them as current.

## Type and text
- No widows or orphans at 1440, 390 and 320: bind the last two words, text-wrap: pretty for body, balance for headings; wrapping lists as even grids.
- Body text flush left, never justified, under 80 characters a line. Contrast 7:1 for text, 4.5:1 for large text.
- Write numbers out ("$2.36 billion", not "$2.36B"). Sets of figures align to the top.
- One numeral style: figures share one face and lining tabular setting, line-height 1.0 or more; a label sits apart from its figure, never touching.
- A phone number is set as an action (tap-to-call, the link style), the same in header, footer and bars.
- One type-spacing scale from tokens in every section; space between groups at least twice the space within.
- State a fact once per block. Long lists of names are never set at display size.

## Colour and image
- Never pair red and green in one palette unless the subject is the holidays.
- Section colours may fill section and header backgrounds when they carry meaning.
- No owner photos: licence-free stock fills every slot from the start; owner shots replace it later. The image brief names each shot's subject, viewpoint, licence and the one treatment that makes the set.
- One rule per treatment: every photo treatment, overlap and texture is applied the same way on every page.

## Originality
- Every project looks like its own subject. uniq.py fails an option that repeats a past project (more than one shared move, the type pair or display face, page form plus grid, or both dominant colours). A palette change alone is never a new design.
- Do not answer "generic" or "common" feedback with a gimmick or a new metaphor. Find and remove the specific pattern.

## Publication
- Sites read as real, finished publications: no operator credit, no visible placeholder labels. [NEW] and open items stay in the hand-off and block packaging.
- No third-party brand marks and no imitation of real brands.
- Showcase graphics (boards, posts, case studies) show each screenshot at the full width of its frame; crop the bottom only.

## Compliance
- Every page the brief's markets require exists, covers its topics in plain words, and is linked from the footer of every page (comply.py). Policy pages are drafts until a lawyer approves them; never mark legal_review done.
- Nothing outside "necessary" runs before a choice: one kit consent banner, reject beside accept with the same look, no ticked boxes, choices reopen from the footer, GPC honoured.
- Every outside host is declared with its purpose; self-host fonts, images and scripts wherever possible.
- A form that collects personal data says why, links the privacy page, and ticks nothing in advance.
- Accessibility claims never exceed what was tested: automated passes are evidence, not conformance.

## Code
- Semantic HTML in landmark and heading order, one CSS file from tokens plus partials, no inline styles, class names prefixed by component (k-, or the partial's own prefix). pass.py checks it.
- Scripts are files: no inline code, event handler attributes or javascript: links, so a strict Content Security Policy holds. CSS uses logical properties (inline, block) so right-to-left needs no new CSS.
- Base list components are block by default; flex or grid rows are opt-in modifiers.
