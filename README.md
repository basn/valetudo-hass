# Valetudo HASS

Home Assistant custom integration for controlling a Valetudo robot via its REST API instead of MQTT.

Status:

- initial scaffold written by Codex against a live Valetudo 2026.02.0 robot
- REST status/control endpoints verified against the robot
- intended for install/testing in Home Assistant next

Current features:

- config flow
- vacuum entity
- authenticated Home Assistant map JSON endpoint for frontend rendering
- segment cleaning via `vacuum.send_command`
- selects for fan speed, water grade, and operation mode
- sensors for battery, status, dock status, segment count, and consumables
- binary sensor for mop attached

Install with HACS as a custom repository or copy `custom_components/valetudo_rest` into your Home Assistant config.

Example segment clean:

```yaml
action: vacuum.send_command
target:
  entity_id: vacuum.valetudo
data:
  command: segment_clean
  params:
    segment_ids:
      - "5"
      - "7"
      - "1"
    iterations: 3
    custom_order: true
```
