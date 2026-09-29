---
type: Failsafe
title: Geofence breach
description: The geofence contains the planned mission, and the action when the vehicle leaves it.
tags: [failsafe, geofence, containment]
checks: [failsafe.geofence_breach, plan.inside_geofence]
table:
  mission_key: geofence_breach
  actions: [RTL, LOITER, LAND, WARN]
  px4_params: [GF_ACTION, GF_MAX_HOR_DIST, GF_MAX_VER_DIST]
  px4_action:
    param: GF_ACTION
    values: {WARN: 1, LOITER: 2, RTL: 3, LAND: 5}
generated:
  by: claude-code
  at: "2026-09-28T20:18:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

Every mission item with a position is inside the inclusion polygon of the plan's geofence
(`plan.inside_geofence`). The mission request declares `failsafes.geofence_breach`, one of
`actions` (`failsafe.geofence_breach`).

On PX4, `GF_ACTION` sets the action. `px4_action` gives its value for each action: WARN is
Warning, LOITER is Hold mode, RTL is Return mode, LAND is Land mode. The bundle does not allow
`GF_ACTION` 4 (Terminate). `GF_MAX_HOR_DIST` and `GF_MAX_VER_DIST` set a cylinder around
Home (0 disables it).

# Source

- S10: §7 Geofence, "Action on Breach: RTL / Loiter / Land / Warn Only".
- S7: parameter reference (v1.17), `GF_ACTION`, `GF_MAX_HOR_DIST`, `GF_MAX_VER_DIST`.
