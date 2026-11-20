## 6. 3D, when the brief asks for it (optional)
img2threejs (Apache-2.0) rebuilds an object from one reference image as procedural Three.js code, with no model file. The kit does not install it: when a direction is 3D by brief, the CD approves it at G3b/G4a, and it is installed for that project only (its own instructions; Node 18 or later and Python 3.10 or later). Then:
- Three.js and the generated code ship as the site's own files (no CDN), so the Content Security Policy stays 'self'.
- The object loads after the first screen is readable and counts against the page-weight budget.
- A still image of the object stands in without script, under reduced motion and while it loads; the still carries the alt text.
- One live 3D context per page. It is the page's moment, never a second one.
