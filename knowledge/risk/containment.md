---
type: Risk Table
title: Containment requirements
description: SORA 2.5 Step 8. The containment robustness from the UA size and speed, the SAIL, and the adjacent-area population limits.
tags: [sora, containment, adjacent-area]
checks: [sora.containment]
table:
  low_below_takeoff_mass_kg: 0.25
  tables:
    - id: "8"
      max_dimension_m: 1
      below_speed_ms: 25
      shelter: true
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: null, assemblies: 40k-to-400k}
        - {below_people_km2: 50000, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [high, medium, low]}
        - {sail: [III], robustness: [medium, low, low]}
        - {sail: [IV, V, VI], robustness: [low, low, low]}
    - id: "9"
      max_dimension_m: 3
      below_speed_ms: 35
      shelter: true
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: null, assemblies: 40k-to-400k}
        - {below_people_km2: 50000, assemblies: under-40k}
        - {below_people_km2: 5000, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, high, medium, low]}
        - {sail: [III], robustness: [out-of-scope, medium, low, low]}
        - {sail: [IV], robustness: [medium, low, low, low]}
        - {sail: [V, VI], robustness: [low, low, low, low]}
    - id: "10"
      max_dimension_m: 3
      below_speed_ms: 35
      shelter: false
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: 50000, assemblies: 40k-to-400k}
        - {below_people_km2: 5000, assemblies: under-40k}
        - {below_people_km2: 500, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, high, medium, low]}
        - {sail: [III], robustness: [out-of-scope, medium, low, low]}
        - {sail: [IV], robustness: [medium, low, low, low]}
        - {sail: [V, VI], robustness: [low, low, low, low]}
    - id: "11"
      max_dimension_m: 8
      below_speed_ms: 75
      shelter: false
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: 50000, assemblies: 40k-to-400k}
        - {below_people_km2: 5000, assemblies: under-40k}
        - {below_people_km2: 500, assemblies: under-40k}
        - {below_people_km2: 50, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, out-of-scope, high, medium, low]}
        - {sail: [III], robustness: [out-of-scope, out-of-scope, medium, low, low]}
        - {sail: [IV], robustness: [out-of-scope, medium, low, low, low]}
        - {sail: [V], robustness: [medium, low, low, low, low]}
        - {sail: [VI], robustness: [low, low, low, low, low]}
    - id: "12"
      max_dimension_m: 20
      below_speed_ms: 120
      shelter: false
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: 50000, assemblies: 40k-to-400k}
        - {below_people_km2: 5000, assemblies: under-40k}
        - {below_people_km2: 500, assemblies: under-40k}
        - {below_people_km2: 50, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, out-of-scope, out-of-scope, high, medium]}
        - {sail: [III], robustness: [out-of-scope, out-of-scope, out-of-scope, medium, low]}
        - {sail: [IV], robustness: [out-of-scope, out-of-scope, medium, low, low]}
        - {sail: [V], robustness: [out-of-scope, medium, low, low, low]}
        - {sail: [VI], robustness: [medium, low, low, low, low]}
    - id: "13"
      max_dimension_m: 40
      below_speed_ms: 200
      shelter: false
      columns:
        - {below_people_km2: null, assemblies: over-400k}
        - {below_people_km2: 50000, assemblies: 40k-to-400k}
        - {below_people_km2: 5000, assemblies: under-40k}
        - {below_people_km2: 500, assemblies: under-40k}
        - {below_people_km2: 50, assemblies: under-40k}
      rows:
        - {sail: [I, II], robustness: [out-of-scope, out-of-scope, out-of-scope, out-of-scope, high]}
        - {sail: [III], robustness: [out-of-scope, out-of-scope, out-of-scope, out-of-scope, medium]}
        - {sail: [IV], robustness: [out-of-scope, out-of-scope, out-of-scope, medium, low]}
        - {sail: [V], robustness: [out-of-scope, out-of-scope, medium, low, low]}
        - {sail: [VI], robustness: [out-of-scope, medium, low, low, low]}
generated:
  by: claude-code
  at: "2026-09-28T20:11:00-07:00"
---
# Rule

A UA with a take-off mass below 250 g gets low containment, with no operational limit for the
adjacent area.

Otherwise, use the first table whose `max_dimension_m` and `below_speed_ms` fit the UA. In
that table, find the row that lists the SAIL. Choose the column from the operational limits:
the average population density allowed in the adjacent area, and the outdoor assemblies
allowed within 1 km of the operational volume. Use the most stringent of the two. The cell
gives the containment robustness. `out-of-scope` means SORA does not support the operation.

The adjacent area extends from the operational volume by the distance flown in 3 minutes at
maximum speed, not less than 5 km and not more than 35 km.

# Source

- S2: AMC1 Article 11, S.4.8.3, Tables 8 to 13 (pp. 38-41).
- S4: §4.8.3, Tables 8 to 13 (pp. 48-51). Origin text.
- S2 Table 8 has three rows (I and II; III; IV, V and VI). S4 Table 8 has four rows with
  "IV - VI" and "V-VI", which overlap. The bundle uses S2.
- S2 Table 12 gives "< 120 m/s"; S4 gives "< 125 m/s". The bundle uses S2.
