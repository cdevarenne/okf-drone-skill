---
type: Hazard
title: GPS signal loss or jamming
description: The UA loses its GNSS position, or the GNSS signal is jammed.
tags: [hazard, gps, gnss, jamming, navigation]
likelihood: 1
severity: 4
residual: Low
generated:
  by: claude-code
  at: "2026-09-28T20:19:00-07:00"
verified:
  - by: "human:cdevarenne"
    at: "2026-09-28T21:00:00-07:00"
---
# Mitigation

- After GPS loss, fly in altitude hold or stabilize mode. See [GPS loss](../failsafes/gps-loss.md).
- Rely on the VO.
- If possible, use visual navigation.

# Residual risk

Low. Likelihood 1, severity 4, score 4 (likelihood x severity).

# Source

- S10: §6 Risk Assessment & Mitigation, row "GPS Signal Loss/Jamming".
