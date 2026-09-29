---
type: MAVLink Command
title: Waypoint (MAV_CMD_NAV_WAYPOINT, 16)
description: Fly to the position in params 5 to 7.
tags: [mavlink, mission-item, nav-waypoint]
table:
  mavlink_id: 16
  name: MAV_CMD_NAV_WAYPOINT
  frame: 3
  params: ["Hold", "Accept Radius", "Pass Radius", "Yaw", "Latitude", "Longitude", "Altitude"]
generated:
  by: claude-code
  at: "2026-09-28T20:15:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

`gen_plan` writes the pattern of the mission type as a list of these commands.

`params` gives the S9 label of each of the seven params. `null` means S9 marks the param
empty. Items with a position use frame 3, `MAV_FRAME_GLOBAL_RELATIVE_ALT`: WGS84 position,
altitude relative to the home position.

See [QGC plan format](../platform/qgc-plan-format.md).

# Source

- S9: MAVLink common message set, `MAV_CMD_NAV_WAYPOINT` (16); `MAV_FRAME` enum.
