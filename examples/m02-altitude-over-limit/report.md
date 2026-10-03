# Mission report: m02-altitude-over-limit

**Proposed decision: NO-GO** (1 failed check, 0 gaps). The tool proposes; a person decides and signs `signoff.yaml`.

## 1. Mission overview

| Mission ID | Mission type | Category | Operation |
|---|---|---|---|
| m02-altitude-over-limit | Infrastructure inspection | open | VLOS |

## 2. Operational details

| Item | Value |
|---|---|
| Takeoff and landing (home) | 44.799, -0.6, 50 m AMSL |
| Maximum altitude | 150 m, relative to home |
| Terrain (declared) | flat |
| Speed | 8 m/s |
| Area vertices | 4 |
| Geofence vertices | 4 |
| UA | MTOM 0.9 kg, 0.35 m, 15 m/s |
| Population density (declared) | sparsely-populated |

## 3. Airspace and regulatory compliance

Airspace, NOTAM, TFR and weather are **declared inputs** in v1. The tool does not check them against a live source. Airspace class G, declared by operator.

| Check | Status | Concept | Evidence | Message |
|---|---|---|---|---|
| alt.max_agl | fail | regulations/easa-open | highest item 150 m above home; terrain flat; limit 120 m | the plan flies above 120 m |
| category.operation | pass | regulations/easa-open | operation VLOS; MTOM 0.9 kg | the operation meets the open-category conditions |
| plan.first_item_takeoff | pass | mavlink/nav-takeoff | first item command 22 | the plan starts with a takeoff |
| plan.last_item_return | pass | mavlink/nav-rtl | last item command 20; allowed [20, 21] | the plan ends with RTL or LAND |
| plan.inside_geofence | pass | failsafes/geofence-breach | 4 items, 4 legs; items outside: none; legs outside: none | the flight path stays inside the geofence |
| failsafe.lost_link | pass | failsafes/lost-link | failsafes.lost_link: RTL | the lost_link action is RTL |
| failsafe.low_battery | pass | failsafes/low-battery | failsafes.low_battery: RTL | the low_battery action is RTL |
| failsafe.critical_battery | pass | failsafes/low-battery | failsafes.critical_battery: LAND | the critical_battery action is LAND |
| failsafe.geofence_breach | pass | failsafes/geofence-breach | failsafes.geofence_breach: RTL | the geofence_breach action is RTL |

## 4. Risk assessment

Hazard matrix (likelihood and severity 1 to 5; score = likelihood x severity):

| Hazard | L | S | Score | Mitigation | Residual |
|---|---|---|---|---|---|
| hazards/gps-jamming | 1 | 4 | 4 | After GPS loss, fly in altitude hold or stabilize mode. See GPS loss.; Rely on the VO.; If possible, use visual navigation. | Low |
| hazards/loss-of-c2 | 2 | 4 | 8 | Set the lost-link failsafe to RTL. See Lost link.; Have a secondary C2 link available.; A visual observer (VO) keeps the UA in visual line of sight (VLOS). | Low |
| hazards/loss-of-vlos | 2 | 3 | 6 | Use VOs.; Plan the flight path inside the visual range.; Use clear communication procedures between the pilot and the VOs. See ARC for the VLOS mitigation. | Low |
| hazards/low-battery | 2 | 3 | 6 | Do a pre-flight battery check.; Monitor the battery voltage during the flight.; Set RTL at the low level and LAND at the critical level. See Low and critical battery. | Low |
| hazards/midair-manned | 1 | 5 | 5 | Monitor ADS-B, if the UA has it.; VOs scan the airspace.; Operate below the open-category height limit. See Open category and ARC. | Low |
| hazards/midair-suas | 2 | 3 | 6 | VOs scan the airspace.; Operate inside the geofence. See Geofence breach.; Coordinate operations with more than one UA. See ARC. | Low |
| hazards/obstacle-ground | 2 | 3 | 6 | Do a pre-flight survey of the area.; Keep a safe altitude.; Use onboard obstacle avoidance, if the UA has it. | Low |
| hazards/payload-malfunction | 2 | 2 | 4 | Do pre-flight payload checks.; Land if the malfunction has an effect on safety. | Low |
| hazards/public-interference | 2 | 2 | 4 | Set up a safety perimeter.; Ground support personnel manage contact with the public. See iGRC for the controlled ground area. | Low |
| hazards/weather-change | 2 | 4 | 8 | Monitor the weather continuously.; Land or do an RTL immediately if the conditions are more than the limits. | Low |

SORA 2.5: not applicable (category open).

## 5. Flight profile and waypoint plan

File `mission.plan` (QGroundControl plan, WGS84). Altitudes in metres relative to home.

| Seq | Command | Frame | Latitude | Longitude | Altitude (m) |
|---|---|---|---|---|---|
| 1 | MAV_CMD_NAV_TAKEOFF | 3 | 44.799 | -0.6 | 150 |
| 2 | MAV_CMD_NAV_WAYPOINT | 3 | 44.7995 | -0.6008 | 150 |
| 3 | MAV_CMD_NAV_WAYPOINT | 3 | 44.8005 | -0.6002 | 150 |
| 4 | MAV_CMD_NAV_WAYPOINT | 3 | 44.8015 | -0.5996 | 150 |
| 5 | MAV_CMD_NAV_RETURN_TO_LAUNCH | 2 |  |  |  |

Failsafe settings (declared; they are vehicle parameters, not part of the plan):

| Failsafe | Declared action | Concept | PX4 parameters |
|---|---|---|---|
| geofence_breach | RTL | failsafes/geofence-breach | GF_ACTION, GF_MAX_HOR_DIST, GF_MAX_VER_DIST |
| lost_link | RTL | failsafes/lost-link | NAV_DLL_ACT, COM_DL_LOSS_T, NAV_RCL_ACT, COM_RC_LOSS_T |
| low_battery | RTL | failsafes/low-battery | COM_LOW_BAT_ACT, BAT_LOW_THR, BAT_CRIT_THR, BAT_EMERGEN_THR |
| critical_battery | LAND | failsafes/low-battery | COM_LOW_BAT_ACT, BAT_LOW_THR, BAT_CRIT_THR, BAT_EMERGEN_THR |

## 6. Decision

Rule (spec §5.5): NO-GO if a check fails; else HOLD if a check is a gap; else GO.

- Failed: `alt.max_agl` (regulations/easa-open): the plan flies above 120 m
- Gaps: none

## 7. Audit trail

| Concept | Title | Verified | Source |
|---|---|---|---|
| failsafes/geofence-breach | Geofence breach | human:cdevarenne 2026-09-28T21:00:00-07:00, human:cdevarenne 2026-10-02T18:37:00-07:00 | S10: §7 Geofence, "Action on Breach: RTL / Loiter / Land / Warn Only". |
| failsafes/lost-link | Lost link | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §7 Failsafe Settings, "Loss of C2 Link: RTL / Land / Loiter". |
| failsafes/low-battery | Low and critical battery | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §7 Failsafe Settings, "Low Battery Trigger ... Action: RTL / Land" and "Critical Battery |
| hazards/gps-jamming | GPS signal loss or jamming | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "GPS Signal Loss/Jamming". |
| hazards/loss-of-c2 | Loss of C2 link | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Loss of C2 Link". |
| hazards/loss-of-vlos | Loss of visual line of sight | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Loss of Visual Line of Sight (VLOS)". |
| hazards/low-battery | Battery failure or low battery | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Battery Failure/Low Battery". |
| hazards/midair-manned | Mid-air collision with manned aircraft | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Mid-Air Collision (Manned Aircraft)". |
| hazards/midair-suas | Mid-air collision with other small UAS | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Mid-Air Collision (Other sUAS)". |
| hazards/obstacle-ground | Collision with a ground obstacle | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Obstacle Collision (Ground)". |
| hazards/payload-malfunction | Payload malfunction | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Payload Malfunction". |
| hazards/public-interference | Public interference or disturbance | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Public Interference / Disturbance". |
| hazards/weather-change | Extreme weather change | human:cdevarenne 2026-09-28T21:00:00-07:00 | S10: §6 Risk Assessment & Mitigation, row "Extreme Weather Change". |
| mavlink/nav-rtl | Return to launch (MAV_CMD_NAV_RETURN_TO_LAUNCH, 20) | human:cdevarenne 2026-09-28T21:00:00-07:00 | S9: MAVLink common message set, `MAV_CMD_NAV_RETURN_TO_LAUNCH` (20); `MAV_FRAME` enum. |
| mavlink/nav-takeoff | Take off (MAV_CMD_NAV_TAKEOFF, 22) | human:cdevarenne 2026-09-28T21:00:00-07:00 | S9: MAVLink common message set, `MAV_CMD_NAV_TAKEOFF` (22); `MAV_FRAME` enum. |
| regulations/easa-open | EASA 'open' category | human:cdevarenne 2026-09-28T21:00:00-07:00 | S1: Reg. (EU) 2019/947, consolidated 2025-05-01, Article 4(1)(b), (d), (e) and 4(2); Annex |
| regulations/easa-specific-sora | EASA 'specific' category and SORA 2.5 | human:cdevarenne 2026-09-28T21:00:00-07:00 | S1: Reg. (EU) 2019/947, consolidated 2025-05-01, Article 5(1) and (2); Article 11(1). |

Pins: OKF `ad30107c31c06aec8a7d5636e0d1058118604e6f`, QGC plan 1 / mission 2, SORA 2.5.

## 8. Approvals

A person fills `signoff.yaml`. The tool leaves every approval field empty.
