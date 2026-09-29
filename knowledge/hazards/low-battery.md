---
type: Hazard
title: Battery failure or low battery
description: The battery fails, or its charge falls below a safe level.
tags: [hazard, battery, energy]
likelihood: 2
severity: 3
residual: Low
generated:
  by: claude-code
  at: "2026-09-28T20:19:00-07:00"
---
# Mitigation

- Do a pre-flight battery check.
- Monitor the battery voltage during the flight.
- Set RTL at the low level and LAND at the critical level.
  See [Low and critical battery](../failsafes/low-battery.md).

# Residual risk

Low. Likelihood 2, severity 3, score 6 (likelihood x severity).

# Source

- S10: §6 Risk Assessment & Mitigation, row "Battery Failure/Low Battery".
