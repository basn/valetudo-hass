"""Constants for the Valetudo REST integration."""

from datetime import timedelta

DOMAIN = "valetudo_rest"
PLATFORMS = ["vacuum", "sensor", "binary_sensor", "select"]
MAP_VIEW_URL = "/api/valetudo_rest/{entry_id}/map"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_NAME = "Valetudo"
DEFAULT_SCAN_INTERVAL = 10
MIN_SCAN_INTERVAL = 5

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)

ATTR_SEGMENT_IDS = "segment_ids"
ATTR_ITERATIONS = "iterations"
ATTR_CUSTOM_ORDER = "custom_order"

COMMAND_SEGMENT_CLEAN = "segment_clean"
COMMAND_LOCATE = "locate"
COMMAND_HOME = "home"
COMMAND_PAUSE = "pause"
COMMAND_STOP = "stop"
COMMAND_START = "start"
