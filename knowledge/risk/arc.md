---
type: Risk Table
title: Air risk class (ARC) and TMPR
description: SORA 2.5 Steps 4 to 6. The initial ARC from the airspace, the VLOS reduction to the residual ARC, and the TMPR.
tags: [sora, arc, air-risk, tmpr, vlos]
checks: [sora.initial_arc, sora.residual_arc]
table:
  initial_arc:
    - {when: {atypical_airspace: true}, arc: a}
    - {when: {above_fl600: true}, arc: b}
    - {when: {airport_environment: true, airspace_class_in: [B, C, D]}, arc: d}
    - {when: {airport_environment: true}, arc: c}
    - {when: {above_500ft_agl: true, mode_c_veil_or_tmz: true}, arc: d}
    - {when: {above_500ft_agl: true, controlled_airspace: true}, arc: d}
    - {when: {above_500ft_agl: true}, arc: c}
    - {when: {mode_c_veil_or_tmz: true}, arc: c}
    - {when: {controlled_airspace: true}, arc: c}
    - {when: {over_urban_area: true}, arc: c}
    - {when: {}, arc: b}
  residual_arc:
    vlos_reduction_classes: 1
    vlos_applies_to: [VLOS, BVLOS-with-airspace-observers]
    lowest_by_vlos: b
  tmpr: {a: none, b: low, c: medium, d: high}
  above_500ft_agl_m: 152.4
generated:
  by: claude-code
  at: "2026-10-02T18:33:24-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:41:00-07:00"
  - by: "human:cdevarenne"
    at: "2026-10-02T18:37:00-07:00"
---
# Rule

The initial ARC comes from the decision tree: use the first entry of `initial_arc` whose
`when` conditions are all true for the operational volume. The last entry has no condition.

Above 500 ft AGL and below FL600, uncontrolled airspace gives ARC-c over urban and over rural
areas. Below 500 ft AGL, uncontrolled airspace over rural areas gives ARC-b.

# Units

The source gives these limits in aviation units, as on aeronautical charts. The keys keep them.

- 500 ft AGL = 152.4 m above ground level (1 ft = 0.3048 m, exact).
- FL600 is a pressure altitude of 60 000 ft (about 18 300 m in the standard atmosphere), not
  a height above ground.

The operator declares `above_500ft_agl` and `above_fl600` as true or false for the operational
volume. The code does no unit conversion. `above_500ft_agl_m` is the metric value of 500 ft
AGL. The code compares the mission `max_altitude_agl_m` with it in one direction only: a
mission that flies above it and declares `above_500ft_agl: false` fails `sora.initial_arc`.
The other direction is valid, because the operational volume (for example its contingency
volume) can go above 500 ft AGL when the planned altitude does not.

For VLOS operations, and for BVLOS operations with airspace observers, the initial ARC can be
reduced by one class. This reduction cannot give ARC-a. Other strategic mitigations (Annex C)
are not in v1.

For BVLOS operations, the TMPR comes from the residual ARC. VLOS is an acceptable tactical
mitigation for all ARC levels.

# Source

- S2: AMC1 Article 11, S.4.4.3, Figure 6 (p. 32); S.4.5.4 (p. 34); S.4.6.3, Table 6 (p. 35).
- S4: §4.4.3, Figure 6 (p. 41); §4.5.4 (pp. 43-44); §4.6.3, Table 6 (p. 45). Origin text.
- S2 extends the VLOS reduction to BVLOS with airspace observers. The bundle uses S2.
