---
type: Regulation
title: EASA 'specific' category and SORA 2.5
description: Outside the 'open' category, an operation needs an authorisation and a SORA assessment.
tags: [easa, specific-category, sora, risk-assessment, operational-authorisation]
checks: [sora.applicable]
table:
  edition: "2.5"
  steps:
    - {step: 1, name: Documentation of the proposed operation}
    - {step: 2, name: Determination of the intrinsic ground risk class (iGRC)}
    - {step: 3, name: Final ground risk class (GRC) determination}
    - {step: 4, name: Determination of the initial air risk class (iARC)}
    - {step: 5, name: Application of strategic mitigations to determine residual ARC}
    - {step: 6, name: Tactical mitigation performance requirement (TMPR) and robustness levels}
    - {step: 7, name: Determination of the specific assurance and integrity level (SAIL)}
    - {step: 8, name: Determination of the containment requirements}
    - {step: 9, name: Identification of the operational safety objectives (OSOs)}
    - {step: 10, name: Comprehensive safety portfolio (CSP)}
generated:
  by: claude-code
  at: "2026-09-28T20:31:00-07:00"
---
# Rule

When an operation does not meet one of the requirements of Article 4 or of Part A of the Annex,
the UAS operator must get an operational authorisation from the competent authority
(Article 5(1)). The operator must do a risk assessment in accordance with Article 11 and send it
with the application (Article 5(2)). A mission with `category: specific` needs this
assessment (`sora.applicable`).

The AMC to Article 11 is SORA 2.5 (`edition`, the same as `SORA_EDITION` in `tools.lock`).
The bundle holds these steps:

- Step 2: [iGRC](../risk/igrc.md)
- Step 3: [M1(A)](../risk/m1a.md), [M1(B)](../risk/m1b.md), [M1(C)](../risk/m1c.md),
  [M2](../risk/m2.md)
- Steps 4 to 6: [ARC and TMPR](../risk/arc.md)
- Step 7: [SAIL](../risk/sail.md)
- Step 8: [Containment](../risk/containment.md)

Step 9 (the OSOs) is not in v1. The check `sora.oso` has no concept, so a specific-category
mission is a coverage gap (HOLD). Steps 1 and 10 are documents that the operator writes.

# Source

- S1: Reg. (EU) 2019/947, consolidated 2025-05-01, Article 5(1) and (2); Article 11(1).
- S2: AMC1 Article 11, S.4.1 to S.4.10 (step names).
- S4: §4 (origin text of SORA 2.5).
