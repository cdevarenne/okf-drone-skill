---
type: MAVLink Command
title: Take off (MAV_CMD_NAV_TAKEOFF, 22)
description: Take off from the ground or from the hand to the altitude in param 7.
tags: [mavlink, mission-item, nav-takeoff]
checks: [plan.first_item_takeoff]
table:
  mavlink_id: 22
  name: MAV_CMD_NAV_TAKEOFF
  frame: 3
  params: ["Pitch", null, "Flags", "Yaw", "Latitude", "Longitude", "Altitude"]
generated:
  by: claude-code
  at: "2026-09-28T20:15:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

The first mission item of a v1 plan is this command (`plan.first_item_takeoff`).

`params` gives the S9 label of each of the seven params. `null` means S9 marks the param
empty. Items with a position use frame 3, `MAV_FRAME_GLOBAL_RELATIVE_ALT`: WGS84 position,
altitude relative to the home position.

See [QGC plan format](../platform/qgc-plan-format.md).

# Source

- S9: MAVLink common message set, `MAV_CMD_NAV_TAKEOFF` (22); `MAV_FRAME` enum.
