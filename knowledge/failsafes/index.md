# Failsafes

Vehicle failsafe settings. They are PX4 parameters, not part of the `.plan` file. v1 checks the
actions that the mission request declares.

* [Lost link](lost-link.md) - loss of the C2 link
* [Low battery](low-battery.md) - low and critical battery
* [Geofence breach](geofence-breach.md) - the vehicle leaves the geofence
* [GPS loss](gps-loss.md) - loss of the position estimate
