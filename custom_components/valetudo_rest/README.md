# Valetudo REST

Small HACS custom integration for Valetudo's REST API.

What it exposes:

- 1 vacuum entity with start/stop/pause/home/locate/fan speed
- 1 rendered map camera from Valetudo REST map data
- `vacuum.send_command` support for segment cleaning
- selects for fan speed, water grade, and operation mode
- sensors for battery, status, dock status, segment count, and consumables
- binary sensor for mop attached

Example `vacuum.send_command` service data:

```yaml
entity_id: vacuum.valetudo
command: segment_clean
params:
  segment_ids:
    - "5"
    - "7"
    - "1"
  iterations: 3
  custom_order: true
```
