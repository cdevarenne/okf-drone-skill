---
type: MAVLink Command
title: Return to launch (MAV_CMD_NAV_RETURN_TO_LAUNCH, 20)
description: Fly back to the launch position. All seven params are empty.
tags: [mavlink, mission-item, nav-rtl]
checks: [plan.last_item_return]
table:
  mavlink_id: 20
  name: MAV_CMD_NAV_RETURN_TO_LAUNCH
  frame: 2
  params: [null, null, null, null, null, null, null]
generated:
  by: claude-code
  at: "2026-09-28T20:15:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

The last mission item of a v1 plan is this command or [Land](nav-land.md) (`plan.last_item_return`).

`params` gives the S9 label of each of the seven params. `null` means S9 marks the param
empty. This item has no position. It uses frame 2, `MAV_FRAME_MISSION`.

See [QGC plan format](../platform/qgc-plan-format.md).

# Source

- S9: MAVLink common message set, `MAV_CMD_NAV_RETURN_TO_LAUNCH` (20); `MAV_FRAME` enum.
