## 3. Smooth and light (S7, S8)
- Animate transform and opacity (clip-path where a reveal needs it). Width, height, top, left, margin and padding force layout on every frame; pass.py --system fails a transition on them, and on "all".
- Predetermined motion in CSS; script only for motion that follows the pointer or can be interrupted. The Web Animations API gives script control at CSS speed with no library.
- Set a transform on the element that moves, not through a custom property on its parent.
- A library is a weight decision: the page budget (brief budget.page_weight_mb) counts it.
- Test slowly: stretch durations several times to see the curve, then on a real phone.
