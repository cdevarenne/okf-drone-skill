---
type: Failsafe
title: Low and critical battery
description: The actions when the battery falls to the low level and to the critical level.
tags: [failsafe, battery, low-battery, critical-battery]
checks: [failsafe.low_battery, failsafe.critical_battery]
table:
  mission_keys: {low: low_battery, critical: critical_battery}
  actions: [RTL, LAND]
  critical_actions: [LAND]
  px4_params: [COM_LOW_BAT_ACT, BAT_LOW_THR, BAT_CRIT_THR, BAT_EMERGEN_THR]
  px4_level:
    low_battery: BAT_CRIT_THR
    critical_battery: BAT_EMERGEN_THR
generated:
  by: claude-code
  at: "2026-09-28T20:18:00-07:00"
---
# Rule

The mission request declares `failsafes.low_battery` (one of `actions`) and
`failsafes.critical_battery` (one of `critical_actions`). A missing value fails
`failsafe.low_battery` or `failsafe.critical_battery`.

The names differ on PX4. PX4 "low" (`BAT_LOW_THR`) is a warning level. PX4 "critical"
(`BAT_CRIT_THR`) commonly triggers Return: it is the mission `low_battery` level. PX4
"emergency" (`BAT_EMERGEN_THR`) commonly triggers Land: it is the mission `critical_battery`
level (`px4_level`). `COM_LOW_BAT_ACT` sets the action.

This concept holds no threshold value. The levels are mission settings.

# Source

- S10: §7 Failsafe Settings, "Low Battery Trigger ... Action: RTL / Land" and "Critical Battery
  Trigger ... Action: Land Immediately".
- S7: parameter reference (v1.17), `COM_LOW_BAT_ACT`, `BAT_LOW_THR`, `BAT_CRIT_THR`,
  `BAT_EMERGEN_THR`.
