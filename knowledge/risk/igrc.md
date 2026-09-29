---
type: Risk Table
title: Intrinsic ground risk class (iGRC)
description: SORA 2.5 Step 2. The iGRC from the UA size and speed and the highest population density in the iGRC footprint.
tags: [sora, grc, igrc, ground-risk, population-density]
checks: [sora.igrc, sora.final_grc]
table:
  columns:
    - {max_dimension_m: 1, max_speed_ms: 25}
    - {max_dimension_m: 3, max_speed_ms: 35}
    - {max_dimension_m: 8, max_speed_ms: 75}
    - {max_dimension_m: 20, max_speed_ms: 120}
    - {max_dimension_m: 40, max_speed_ms: 200}
  rows:
    - {band: controlled-ground-area, below_people_km2: null, igrc: [1, 1, 2, 3, 3]}
    - {band: remote, below_people_km2: 5, igrc: [2, 3, 4, 5, 6]}
    - {band: lightly-populated, below_people_km2: 50, igrc: [3, 4, 5, 6, 7]}
    - {band: sparsely-populated, below_people_km2: 500, igrc: [4, 5, 6, 7, 8]}
    - {band: suburban, below_people_km2: 5000, igrc: [5, 6, 7, 8, 9]}
    - {band: high-density-metropolitan, below_people_km2: 50000, igrc: [6, 7, 8, 9, 10]}
    - {band: assemblies-of-people, below_people_km2: null, igrc: [7, 8, null, null, null]}
  small_ua: {max_takeoff_mass_kg: 0.25, max_speed_ms: 25, igrc: 1, not_over_assemblies: true}
  final_grc_floor: controlled-ground-area
generated:
  by: claude-code
  at: "2026-09-28T20:11:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

Find the iGRC at the intersection of the highest population density band in the iGRC
footprint and the left-most column where the UA maximum characteristic dimension and the UA
maximum speed are both within the column values. A `null` cell is not part of SORA: the
operation is outside the scope of SORA (certified category).

A single UA with a take-off mass of 250 g or less and a maximum speed of 25 m/s or less has an
iGRC of 1, unless it operates over assemblies of people (`small_ua`).

The final GRC is the iGRC plus the credits of the applied mitigations, in numerical sequence.
The M1 mitigations cannot reduce the final GRC below the value in the `controlled-ground-area`
row of the same column (`final_grc_floor`).

A final GRC above 7 is outside SORA. See [SAIL](sail.md).

# Bands

The band names come from the qualitative descriptors: controlled ground area or extremely
remote; remote; lightly populated; sparsely populated or residential lightly populated;
suburban or low-density metropolitan; high-density metropolitan; assemblies of people.

# Source

- S2: AMC1 Article 11, S.4.2.3 Table 1 (iGRC) and Table 2 (qualitative descriptors),
  pp. 24-26; S.4.3.4 (M1 floor).
- S4: §4.2, Table 2 (p. 34) and Table 3 (p. 36); §4.3.4(f) (p. 39). Origin text.
- S2 adds "unless operating over assemblies of people" to the 250 g rule. The bundle uses S2.
