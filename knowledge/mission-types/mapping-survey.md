---
type: Mission Type
title: Mapping survey
description: Cover an area in parallel lines to map it.
tags: [mission-type, mapping, survey, grid]
table:
  pattern: grid
generated:
  by: claude-code
  at: "2026-09-28T20:11:00-07:00"
---
# Rule

`gen_plan` uses the `grid` pattern for this mission type. The plan starts with a takeoff,
flies the pattern inside the mission area, and ends with a return to launch. See
[QGC plan format](../platform/qgc-plan-format.md).

# Source

- S10: §1 Mission Type; §7 Mapping/Survey Specific Parameters: Pattern Type (Grid).
