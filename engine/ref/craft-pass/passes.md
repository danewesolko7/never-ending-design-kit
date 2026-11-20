## Before the passes
- **Register check.** Write one sentence each on the reader, the voice and the aesthetic. Then check that the type, image and colour choices speak in that register. For example, readers new to a subject and a plain voice call for an editorial register, not a technical one, even when the subject is technical.
- **Page furniture.** Define the furniture once: kicker or section number, headline, standfirst, body, subhead, figure, caption, source line, pull figure or quote, link style, section end and page end (next reads, sources, colophon). Every section uses this set; a section invents nothing new.
- **Benchmarks beside the work.** Open two benchmark captures from `out/bench/` at the same width as the comp.

## Pass 1: type
- **Scale:** about five size levels. Weight and space do the rest. Write the scale down.
- **Display type:** kern by eye where the font's spacing fails at large sizes, tighten tracking as the size grows, and break lines for sense, keeping each phrase whole on its line (never split an adjective from its noun or a number from its unit).
- **Text:** a measure of 60 to 75 characters, line spacing of 1.5 (AAA), flush left, and a good rag (no steps or wedges). No widows or orphans at 1440, 390 or 320.
- **Details:** true quotes and apostrophes, en and em dashes, non-breaking spaces between number and unit and in short names. Tabular lining numerals in tables and figures; proportional numerals in text. Small caps or letterspaced labels used only where the system says.
- **Hang punctuation and align optically:** large type's stems line up with the column edge, not its sidebearings.

## Pass 2: space and image
- **One spacing scale,** with vertical rhythm. Space between groups is at least twice the space within. Section transitions are designed, not just padding.
- **Edges:** no near misses (2 to 12px). Everything aligns to the grid or breaks it clearly (design-foundations section 3).
- **Images:** chosen as a picture editor would: strong, specific and few. Each is cropped hard to its point, treated consistently and lightly, captioned (what and where) and credited (source and licence).
- **Diagrams:** one grammar for every figure: stroke, arrow, label size and position, and the colour roles. Labels are real words at a readable size. Each diagram teaches the point its caption states.

## Pass 3: finish
- **States:** hover, focus (a visible 3px ring), visited, active, and the current page in the nav.
- **Chrome:** the header, nav, phone menu and footer are designed, not kit defaults.
- **Phone:** composed for 390 in its own right, and checked at 320.
- **Edge cases:** long words, 200% zoom, no image, slow fonts (fallback metrics close to the face).
- **Consistency sweep:** every repeated element is identical everywhere.

## Each pass
List what you found (location, issue, fix), fix it in the kit source, rebuild, and save before and after crops (`node tools/shot.js` on the page, cropped to the element) for the three most visible changes. Then run design-review on the result. A pass that finds nothing has not looked closely enough.
