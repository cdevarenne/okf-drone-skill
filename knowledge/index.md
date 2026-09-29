---
okf_version: "0.2"
---
# OKF Drone Mission Knowledge Bundle

Knowledge graph that grounds the `drone-mission-compliance` skill. Every check and every score
that the skill writes cites a concept here. A check or a score with no concept is a coverage
gap. It is never a default value.

# Map

* [Regulations](regulations/) - EU rules: the 'open' category limits, the 'specific' category and SORA 2.5
* [Risk](risk/) - SORA 2.5 tables (iGRC, ARC, SAIL, containment) and ground-risk mitigations
* [Hazards](hazards/) - the flight-plan risk matrix: likelihood, severity, mitigation
* [Failsafes](failsafes/) - lost link, battery, geofence and GPS-loss actions, with PX4 parameters
* [MAVLink](mavlink/) - the mission item commands that a v1 plan uses
* [Mission types](mission-types/) - the flight pattern for each mission type
* [Platform](platform/) - the QGroundControl plan file format
