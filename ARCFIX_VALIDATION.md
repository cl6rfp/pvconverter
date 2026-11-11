# Arc direction correction – validation

The SVG preview resolves route-arc direction from the ordered route primitive stream.
For each arc, it evaluates both possible route traversal orientations (stored start-to-end
and end-to-start) and compares the corresponding arc tangents with adjacent connected
line segments. The selected sweep is display-only; source PV blocks are not modified.

Validation on the included R1.0 PV fixture:
- PVF integrity and source SHA-256: OK
- Components: 2,693
- Shapes: 112
- Pins: 11,104
- Pads: 347
- Padstacks: 228
- Nets: 1,997
- Routes: 1,997
- Segments: 94,146
- Vias: 7,149
- Route primitives: 101,295
- Artwork groups: 204
- Mechanical holes: 7
- Arc records reviewed: 27,729
- Route arcs with direction inferred from continuity: 25,475
- Route arcs using ambiguous display fallback: 1,962
- Arcs without connected line tangent evidence: 1,947
- Routes traversing stored arcs end-to-start: 12,708
- SVG export: OK (11,026,037 bytes)
- Synthetic forward- and reverse-traversal arc-direction unit tests: PASS
- PVF, geometry and Python syntax tests: PASS

Important: the GenCAD records parsed by this version contain arc start, end and center,
but no explicit direction token. Where adjacent route geometry cannot distinguish the
candidate sweeps, the SVG uses a conservative minor-arc display fallback. These cases
remain identified in the diagnostic report rather than being presented as source-confirmed.


## ARCFIX4 – SVG sweep flag under Y reflection

A rendering-direction defect was found after ARCFIX3: the SVG root group uses
`scale(1,-1)`, so the SVG sweep flag must be inverted relative to the GenCAD
Y-up sweep. The renderer now maps positive/CCW sweeps to SVG flag 1 and negative/CW
sweeps to flag 0. This corrects which side of the chord the arc is drawn on without
changing the PV source geometry. The synthetic test asserts both mappings.

The reference-board fixture-level export should be regenerated with the commands
in the README to inspect the corrected visual result; the ARCFIX3 counts above are
historical and are not presented as a new ARCFIX4 fixture run.
