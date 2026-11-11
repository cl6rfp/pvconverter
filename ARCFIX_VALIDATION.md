# Arc direction correction – validation

The SVG preview now chooses route-arc direction using the ordered route primitive stream.
For each arc it compares the tangent at the start/end against adjacent connected line
segments. The source PV blocks are not modified; the selected sweep is display-only.

Validation on the included R1.0 PV fixture:
- PVF integrity and source SHA-256: OK
- Routes: 1,997
- Segments: 94,146
- Vias: 7,149
- Route primitives: 101,295
- Arc records in full geometry report: 27,729
- Route arcs assigned direction from neighboring continuity: 12,942
- Route arcs requiring conservative minor-arc fallback: 14,495
- SVG export: OK (11,025,389 bytes)
- Synthetic arc-direction unit tests: PASS

Important: the GenCAD records parsed by this version contain arc start, end and center,
but no explicit direction token. Where adjacent route geometry does not provide a
clear tangent preference, the SVG uses a minor-arc fallback. These ambiguous cases
are intentionally reported rather than silently presented as source-confirmed.
