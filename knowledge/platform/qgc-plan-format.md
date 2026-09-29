---
type: Reference
title: QGroundControl plan file format
description: The JSON .plan file that QGroundControl loads. v1 writes a subset of it.
tags: [qgc, plan-format, mission, geofence]
generated:
  by: claude-code
  at: "2026-09-28T20:11:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

A `.plan` file is JSON with `fileType: Plan`, a `mission` (items), a `geoFence` (circles and
polygons) and `rallyPoints`. The versions are pinned in `tools.lock`.

v1 writes only `SimpleItem` mission items and inclusion polygons. The vendored subset schema
`tests/fixtures/qgc/plan.schema.json` is the contract. Circle fences and `ComplexItem` are not
in v1.

# Source

- S8: QGroundControl plan file format (master). The polygon `version` is 2 in the table and 1
  in the example; the subset schema accepts both.
