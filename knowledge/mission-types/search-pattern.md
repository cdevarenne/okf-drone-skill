---
type: Mission Type
title: Search pattern
description: Search an area from a datum outward.
tags: [mission-type, search, expanding-square]
table:
  pattern: expanding-square
generated:
  by: claude-code
  at: "2026-09-28T20:11:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

`gen_plan` uses the `expanding-square` pattern for this mission type. The plan starts with a takeoff,
flies the pattern inside the mission area, and ends with a return to launch. See
[QGC plan format](../platform/qgc-plan-format.md).

# Source

- S10: §1 Mission Type; §7 Reconnaissance Specific Parameters: Search Pattern (Expanding Square).
