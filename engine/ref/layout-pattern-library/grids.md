## 1. Grid systems (one per page, chosen deliberately)
- **Manuscript**: one text block with generous margins.
- **Column**: 12 columns with gutters; content spans different counts.
- **Modular**: columns plus rows, with spatial zones grouping modules.
- **Hierarchical**: modules sized by importance.
- **Baseline**: a shared vertical rhythm under any of the above.
- **Nested**: a different grid inside each section, within the page grid (Samara, *Making and Breaking the Grid*; see graphic-art-direction).
- Never end an element in a gutter. Break the grid deliberately, and say why.
- CSS: `grid-template-columns: repeat(12, minmax(0, 1fr))`, `subgrid` for nested alignment, collapse under about 800px, and never `margin: 0` on a centred grid container.
