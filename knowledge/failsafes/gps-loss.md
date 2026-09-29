---
type: Failsafe
title: GPS loss
description: The action when the position estimate becomes invalid, for example after GPS loss.
tags: [failsafe, gps, gnss, position-loss]
table:
  actions: [LAND, ALT_HOLD, STABILIZE]
  px4_params: [EKF2_NOAID_TOUT, COM_POS_FS_EPH]
generated:
  by: claude-code
  at: "2026-09-28T20:18:00-07:00"
---
# Rule

v1 has no check for this failsafe: the mission request declares no GPS-loss action. The
concept records the actions and the PX4 trigger parameters. The GPS-loss hazard links to it.

On PX4, `EKF2_NOAID_TOUT` (us) is the maximum dead-reckoning time before the horizontal
position is invalid. `COM_POS_FS_EPH` (m) is the horizontal position error that triggers the
failsafe on hovering vehicles.

# Source

- S10: §7 Failsafe Settings, "Loss of GPS: Land / Altitude Hold / Stabilize".
- S7: parameter reference (v1.17), `EKF2_NOAID_TOUT`, `COM_POS_FS_EPH`.
