---
type: Risk Table
title: SAIL determination
description: SORA 2.5 Step 7. The SAIL (I to VI) from the final GRC and the residual ARC.
tags: [sora, sail]
checks: [sora.sail]
table:
  arc_columns: [a, b, c, d]
  rows:
    - {final_grc_max: 2, sail: [I, II, IV, VI]}
    - {final_grc_max: 3, sail: [II, II, IV, VI]}
    - {final_grc_max: 4, sail: [III, III, IV, VI]}
    - {final_grc_max: 5, sail: [IV, IV, IV, VI]}
    - {final_grc_max: 6, sail: [V, V, V, VI]}
    - {final_grc_max: 7, sail: [VI, VI, VI, VI]}
  above_table: certified-category
generated:
  by: claude-code
  at: "2026-09-28T20:11:00-07:00"
---
# Rule

Use the first row whose `final_grc_max` is equal to or more than the final GRC, and the column
of the residual ARC. A final GRC above the last row puts the operation in the certified
category.

# Source

- S2: AMC1 Article 11, S.4.7.3, SAIL determination table, p. 38 (the table caption reads
  "Table 3"; the text calls it Table 7).
- S4: §4.7.3, Table 7 (p. 47). Origin text. The values are the same.
