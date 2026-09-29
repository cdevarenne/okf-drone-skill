---
type: Hazard
title: Loss of C2 link
description: The command and control link to the UA stops during the mission.
tags: [hazard, c2, comms, lost-link]
likelihood: 2
severity: 4
residual: Low
generated:
  by: claude-code
  at: "2026-09-28T20:19:00-07:00"
---
# Mitigation

- Set the lost-link failsafe to RTL. See [Lost link](../failsafes/lost-link.md).
- Have a secondary C2 link available.
- A visual observer (VO) keeps the UA in visual line of sight (VLOS).

# Residual risk

Low. Likelihood 2, severity 4, score 8 (likelihood x severity).

# Source

- S10: §6 Risk Assessment & Mitigation, row "Loss of C2 Link".
