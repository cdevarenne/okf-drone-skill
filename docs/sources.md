# Sources

Every regulatory value in `knowledge/` comes from a document in this table.
The owner reads each document and sets `Status` to `read` with the date.
A concept can cite only a document with status `read`.

| Id | Document | Edition / date | URL | Needed for | Status |
|---|---|---|---|---|---|
| S1 | Commission Implementing Regulation (EU) 2019/947 | consolidated 2025-05-01 | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02019R0947-20250501 | `regulations/easa-open`, `regulations/easa-specific-sora` | read 2026-09-28 |
| S2 | EASA ED Decision 2025/018/R, Annex (AMC & GM to Reg. 2019/947, Issue 1, Amendment 4; SORA 2.5) | 15 Sep 2025; corrigendum 12 Dec 2025 | https://easa.europa.eu/en/document-library/agency-decisions/ed-decision-2025018r | applicability and transition dates | read 2026-09-28 |
| S3 | EASA Easy Access Rules for UAS | revision of June 2026 | https://www.easa.europa.eu/en/document-library/easy-access-rules/easy-access-rules-unmanned-aircraft-systems-regulations-eu | consolidated AMC text | read 2026-09-28 |
| S4 | JARUS SORA 2.5 Main Body (JAR_doc_25) | 2.5 | http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Main-Body-Release-JAR_doc_25.pdf | `risk/igrc`, `risk/arc`, `risk/sail`, `risk/containment`, M1(A)/M1(B)/M1(C), M2, M3 status, OSO list | read 2026-09-28 |
| S5 | JARUS SORA 2.5 Annex E (JAR_doc_28) | 2.5 | http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Annex-E-Release.JAR_doc_28pdf.pdf | OSO robustness | read 2026-09-28 |
| S6 | JARUS SORA 2.5 Annex F (JAR_doc_29) | 2.5 | http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Annex-F-Release.JAR_doc_29pdf.pdf | critical-area model for non-typical UA (not needed for the v1 iGRC table) | read 2026-09-28 |
| S7 | PX4 parameter reference and safety (failsafes) page | v1.17 | https://docs.px4.io/v1.17/en/advanced_config/parameter_reference and https://docs.px4.io/v1.17/en/config/safety_intro | `failsafes/*` parameter names | read 2026-09-28 |
| S8 | QGroundControl plan file format | master | https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html | `platform/qgc-plan-format`, `tests/fixtures/qgc/plan.schema.json` | read 2026-09-28 by agent; read 2026-09-28 by cdevarenne |
| S9 | MAVLink common message set | master | https://mavlink.io/en/messages/common.html | `mavlink/*` command ids and parameters | unread |
| S10 | Comprehensive Drone Flight Plan Template (owner input; kept outside the repo) | 1.0 | none | `hazards/*`, `mission-types/*`, failsafe actions | read 2026-09-28 by cdevarenne |

## Local copies

Downloaded by the owner on 2026-09-28 (local time). Kept outside the repo; not redistributed.

| File | Source | Download page | Bytes | SHA-256 |
|---|---|---|---|---|
| `annex_to_ed_decision_2025-018-r_1.pdf` | S2 | https://www.easa.europa.eu/en/downloads/142514/en | 3448513 | `4733d5501b55297ed2b27cd8dceeb1eee3268af05f9421318bc54b452f83999e` |
| `corrigendum_to_ed_decision_2025-018-r.pdf` | S2 | https://www.easa.europa.eu/en/downloads/142969/en | 167350 | `b810d348896c3cecf34365e41a9275533f8e13649659f2d2872f48ed35119ff3` |
| `SORA-v2.5-Main-Body-Release-JAR_doc_25.pdf` | S4 | http://jarus-rpas.org/wp-content/uploads/2024/06/SORA-v2.5-Main-Body-Release-JAR_doc_25.pdf | 1344663 | `2471913e55c38999dc5ba0894ac696c3e4722ddb0956b1c62f15e6fbd9a1be1c` |

The Decision itself (2 pages, not stored locally): https://www.easa.europa.eu/en/downloads/142510/en.
Per that text (read by agent 2026-09-28, confirmed by cdevarenne 2026-09-28), the Decision enters into force on its
publication in the EASA Official Publication.

EASA SORA overview page (links to the SORA 2.5 package):
https://www.easa.europa.eu/en/domains/drones-air-mobility/operating-drone/specific-category-civil-drones/specific-operations-risk-assessment-sora#group-easa-downloads

## Findings checked in S4

These come from a secondary source (https://eudroneport.com/blog/sora-2-5-european-uas-operations/).

1. M1 is split into M1(A) sheltering, M1(B) operational restrictions, M1(C) ground observation.
2. Intrinsic GRC uses population density and a critical-area calculation (Annex F).
3. Containment has low, medium and high levels.

Findings 1 to 3: confirmed in S4 by cdevarenne 2026-09-28.

Checked 2026-09-28 in S4 (agent, text extraction and page images). Confirmed by cdevarenne
2026-09-28.

- M3: S4 change log (edition 2.5) says "Removal of ERP as a mitigation". S4 Table 5 lists only
  M1(A), M1(B), M1(C) and M2. S2 OSO #08 names the ERP as Criterion #4.
- SAIL: S4 §4.7, Table 7 (p. 47): final GRC x residual ARC -> SAIL I to VI; final GRC > 7 is
  Category C (certified).
- Containment: S4 §4.8, Tables 8 to 13 (pp. 49-51), by UA size, SAIL, adjacent-area population
  and outdoor assemblies. Table 8 rows read "IV - VI" and "V-VI"; confirmed on the page.
- OSOs: S4 §4.9.3, Table 14 (p. 54): 17 OSOs (#01-#09, #13, #16-#20, #23, #24).
- S2 and S4 differ: OSO #04 is L/M/H for SAIL IV/V/VI in S4 and M/H/H in S2 (p. 44). The
  dependency columns also differ. The bundle uses S2 values and cites S4 as origin.

Population density bands: found 2026-09-28 in S2 (AMC Issue 1, Amendment 3, Table 1 and
Table 2, pages 23-25) and S4 (Table 2 and Table 3, pages 34-36). The iGRC values are the same in
both. Bands: controlled ground area, < 5, < 50, < 500, < 5 000, < 50 000, > 50 000 people/km2.
Confirmed by cdevarenne 2026-09-28.

Resolved 2026-09-28: the corrigendum to ED Decision 2025/018/R (12 December 2025, 1 page) only
renames the annex. "AMC and GM to Reg. (EU) 2019/947 — Issue 1, Amendment 3" becomes
"Issue 1, Amendment 4". It changes no text or table. Decision date: 15 September 2025.
Cite S2 as "AMC & GM to Reg. (EU) 2019/947, Issue 1, Amendment 4 (ED Decision 2025/018/R, as
corrected 12 December 2025)". The downloaded annex does not state an applicability date.

## Differences between S2 and S4 (Phase 1)

Found 2026-09-28 by agent in the local copies (SHA-256 match). The bundle uses S2.

| Topic | S2 (AMC1 Art. 11) | S4 (JARUS main body) |
|---|---|---|
| 250 g rule for iGRC 1 | adds "unless operating over assemblies of people" (p. 24) | no exception (p. 34) |
| Containment Table 8 rows | I & II; III; IV, V & VI (p. 39) | I & II; III; "IV - VI"; "V-VI", which overlap (p. 49) |
| Containment Table 12 speed | < 120 m/s (p. 41) | < 125 m/s (p. 50) |
| VLOS ARC reduction | VLOS and BVLOS with airspace observers (p. 34) | VLOS and pilot with an observer alongside (p. 43) |
| SAIL table caption | "Table 3" (p. 38); the text calls it Table 7 | Table 7 (p. 47) |

The iGRC, Table 5 credits, TMPR and SAIL values are the same in S2 and S4.

## Known discrepancy in S8

The geofence polygon table says "Documented version is 2", but the polygon example uses
`"version": 1`. The subset schema accepts both.
