# Output templates

gate.py builds the gate packet, usage line and state.md from the hand-off and the log. The model writes only the hand-off and the data files.

HAND-OFF  docs/stages/<n>.md  (<=250 words, delta only; batches: 8-1.md, 8-2.md)
stage: <n> | status: done | date: <YYYY-MM-DD>
decided: <one line each>
new files: <paths, comma separated, relative to the project>
open: <item> | owner (CD or client) | due  (one line each, or none)
next reads: <paths>
decide: <G-gate>: <one question> | choices: <a / b / c> | unlocks: <next stage>   (write the gate once; gate.py does not repeat it)
options: <n made>   (optional)   revisions: <n>   (optional)

FINGERPRINT  fingerprints/<option>.json  (fixed keys, values <=4 words; type_pair exempt)
{"form":"","grid":"","hero":"","nav":"","type_pair":"","type_class":"","movement":"","hues":["#hex","#hex"],"roles":"","image":"","texture":"","moves":["",""],"motion":"","scope":"project"}
"movement" names the design movement the option draws on (catalogue.json movements, or none); seed.py marks it used.
Page fingerprints: {"scope":"page","moves":["<the page's signature technique>"]} as fingerprints/page-<id>.json.
Concept fingerprints: fingerprints/c<n>.json; direction fingerprints: fingerprints/d<n>.json. The chosen direction's fingerprint is
copied to fingerprints/chosen.json after G3b/G4a.

CONCEPT OR DIRECTION CARD  docs/cards/c<n>.md or d<n>.md  (<=150 words; 3 per choice gate, each with its rough or board)
name: <2-4 words> | seed: <unused seed> | artefact: <subject artefact>
idea: <one sentence>
<4-6 fields, one line each: type pair + alternate, colour roles, image treatment, signature move, voice line, motion moment>
fingerprint: fingerprints/<option>.json

IMAGE BRIEF  image-brief.json  (one row per image slot)
{"slot":"","subject":"","viewpoint":"","source":"stock|client|shoot","source_url":"","author":"","licence":"","treatment":"","status":"placeholder|sourced","file":"","alt":"","w":1600,"h":1000}

REFERENCE  references.jsonl  (one row per reference; tools/refs.py --check)
{"sweep":"A|B|C","section":1,"title":"","url":"https://","seen":"YYYY-MM-DD","technique":"","use":"","used":false}

INTERACTION SPEC  interaction.json  (one row per component)
{"component":"","states":["hover","focus","active","disabled","error"],"keyboard":"","motion":"","reduced_motion":""}

GATE CHECKLIST  built by gate.py --checklist (no model prose)
<each of the 9 taste questions>: <script answer, or CD>

DATA SCHEMAS
brief.json      project, site_name, key_page, lang, goals[], audience, pages_hint[], brand_assets[], benchmarks[],
                constraints[], deadline, budget{credits, unit, page_weight_mb, reading_level}, wcag (AAA default, or AA), lean_mode, client{name, role}, open[]
content.json    pages[{id, title, purpose, sections[{id, purpose, fact_ids[], form, words}]}]
structure.json  page_form, grid{columns, gutter, margin, nested[]}, sections[{id, block, span, order, rhythm, ground}], breakpoints[]
                (block items: t, start, span, words, size, h, bleed, phone; see tools/greek.py --help)
tokens.json     color{<role>: hex}, type{faces[{family, source, licence, alternate, role, files[{file, weight}]}], scale[], roles{}},
                space[], radius[], states{}, motion{durations[], easing, reduced}, breakpoints[]
pages/<p>.json  id, title, nav?, meta{title, description, og_image}, sections[{id, primitive|partial, variant?, text{<field>: string}, images[<slot>]}]
                (see tools/build.py --help for field names and partial placeholders)
