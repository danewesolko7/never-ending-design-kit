## 3. Consent and outside services (S7, S8)
The kit applies one standard everywhere, the strictest: nothing outside "necessary" runs before the visitor chooses.
- The banner is the kit's (build.py, primitives/consent.js and consent.css), on whenever a third party outside "necessary" is declared. Style it only through tokens. Never add a second banner or a vendor's.
- First layer: reject all and accept all side by side, same class, same size, same words weight; "choose" opens the categories, none ticked. No pre-ticked boxes, no "by using this site you agree", no wall, no nagging.
- A region, not a modal: the page stays usable while it waits. With no script, nothing loads.
- Gate every outside script: script type="text/plain" data-consent="<category>" data-src="<url>" (data-integrity for a fixed file). Gate embeds the same way: iframe data-consent="media" data-src, with a plain link beside it so the content is reachable without consent.
- A Global Privacy Control signal keeps marketing off and says so.
- The footer's cookie settings button reopens the choices on every page.
- Every host the site calls is declared in brief.json compliance.third_parties; comply.py fails one that is not, and one that loads before a choice.
- Self-host fonts, images and scripts wherever possible: a host never called needs no consent, no notice and no transfer.
