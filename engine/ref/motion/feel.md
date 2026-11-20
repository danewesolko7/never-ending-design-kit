## 2. Easing, duration and physicality (S7 tokens, S8 partials)
- Easing: things arriving or leaving use a strong ease-out (fast start); things moving on screen use ease-in-out; colour and hover use ease; constant motion is linear. Never ease-in on interface motion: it holds back the moment the reader is watching. Built-in curves are weak; put two custom curves in tokens.json motion.easing.
- Duration: press feedback 100 to 160ms; tooltips and small popovers 125 to 200ms; menus 150 to 250ms; dialogs and drawers 200 to 500ms. Interface motion stays under 300ms; only the opening moment may run longer.
- Physicality: nothing grows from scale(0); start at 0.9 to 0.97 with opacity 0. A pressed control scales to about 0.97. Popovers grow from their trigger; dialogs from the centre.
- Interrupting: use transitions for anything that can be triggered again mid-way (they retarget); keyframes restart from zero. @starting-style gives an entry without script.
- Groups: stagger 30 to 80ms, never blocking input. Uneven delays read as natural.
- Two states that overlap in a crossfade can be blended with a blur of a few pixels during the change.
