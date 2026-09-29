---
type: MAVLink Command
title: Land (MAV_CMD_NAV_LAND, 21)
description: Land at the position in params 5 and 6.
tags: [mavlink, mission-item, nav-land]
table:
  mavlink_id: 21
  name: MAV_CMD_NAV_LAND
  frame: 3
  params: ["Abort Alt", "Land Mode", null, "Yaw Angle", "Latitude", "Longitude", "Altitude"]
generated:
  by: claude-code
  at: "2026-09-28T20:15:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

A v1 plan can end with this command instead of [Return to launch](nav-rtl.md).

`params` gives the S9 label of each of the seven params. `null` means S9 marks the param
empty. Items with a position use frame 3, `MAV_FRAME_GLOBAL_RELATIVE_ALT`: WGS84 position,
altitude relative to the home position.

See [QGC plan format](../platform/qgc-plan-format.md).

# Source

- S9: MAVLink common message set, `MAV_CMD_NAV_LAND` (21); `MAV_FRAME` enum.
