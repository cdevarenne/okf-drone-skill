---
type: Regulation
title: EASA 'open' category
description: The requirements for an operation in the 'open' category of Reg. (EU) 2019/947.
tags: [easa, open-category, height-limit, vlos, mtom]
checks: [alt.max_agl, category.operation]
table:
  max_height_above_surface_m: 120
  below_takeoff_mass_kg: 25
  operations: [VLOS]
generated:
  by: claude-code
  at: "2026-09-28T20:31:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"  
---
# Rule

An operation is in the 'open' category only if it meets all the requirements of Article 4(1).
v1 checks three of them:

- During flight, the UA stays within 120 m of the closest point of the surface of the earth
  (`max_height_above_surface_m`, check `alt.max_agl`). Over natural elevations, the distance
  is measured from the terrain (UAS.OPEN.010(2)).
- The UA has a maximum take-off mass of less than 25 kg (`below_takeoff_mass_kg`).
- The remote pilot keeps the UA in VLOS at all times (`operations`, check
  `category.operation`).

An operation that does not meet a requirement of Article 4 is in the 'specific' category. See
[Specific category and SORA](easa-specific-sora.md).

# Not in v1

The exceptions are not modeled: overflight of an obstacle (UAS.OPEN.010(3)), follow-me mode and
UA observers (Article 4(1)(d)), and unmanned sailplanes (UAS.OPEN.010(4)). The subcategories
A1, A2 and A3 and the requirements for people, dangerous goods and dropped material are not
checked. A mission that needs one of these is outside v1.

# Source

- S1: Reg. (EU) 2019/947, consolidated 2025-05-01, Article 4(1)(b), (d), (e) and 4(2); Annex
  Part A, UAS.OPEN.010(2) to (4).
