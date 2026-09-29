---
type: Failsafe
title: Lost link
description: The action when the command and control (C2) link to the ground station is lost.
tags: [failsafe, c2, lost-link, datalink]
checks: [failsafe.lost_link]
table:
  mission_key: lost_link
  actions: [RTL, LAND, LOITER]
  px4_params: [NAV_DLL_ACT, COM_DL_LOSS_T, NAV_RCL_ACT, COM_RC_LOSS_T]
  px4_action:
    param: NAV_DLL_ACT
    values: {LOITER: 1, RTL: 2, LAND: 3}
generated:
  by: claude-code
  at: "2026-09-28T20:18:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Rule

The mission request declares `failsafes.lost_link`. The value is one of `actions`. A mission
with no lost-link action fails `failsafe.lost_link`.

On PX4, `NAV_DLL_ACT` sets the action when the ground station (data) link is lost, after the
time in `COM_DL_LOSS_T` (s). `NAV_RCL_ACT` and `COM_RC_LOSS_T` do the same for the manual
control (RC) link. `px4_action` gives the `NAV_DLL_ACT` value for each action: LOITER is
PX4 Hold mode, RTL is Return mode, LAND is Land mode.

# Source

- S10: §7 Failsafe Settings, "Loss of C2 Link: RTL / Land / Loiter".
- S7: parameter reference (v1.17), `NAV_DLL_ACT`, `COM_DL_LOSS_T`, `NAV_RCL_ACT`,
  `COM_RC_LOSS_T`.
