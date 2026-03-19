"""Sensor platform for Valetudo REST."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ValetudoCoordinator
from .entity import ValetudoRestEntity


@dataclass(frozen=True, kw_only=True)
class ValetudoSensorDescription(SensorEntityDescription):
    """Valetudo sensor description."""

    value_key: str


SENSORS: tuple[ValetudoSensorDescription, ...] = (
    ValetudoSensorDescription(
        key="battery",
        name="Battery",
        value_key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
    ),
    ValetudoSensorDescription(
        key="status",
        name="Status",
        value_key="status",
    ),
    ValetudoSensorDescription(
        key="status_flag",
        name="Status flag",
        value_key="status_flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ValetudoSensorDescription(
        key="dock_status",
        name="Dock status",
        value_key="dock_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ValetudoSensorDescription(
        key="operation_mode",
        name="Operation mode",
        value_key="operation_mode",
    ),
    ValetudoSensorDescription(
        key="water_grade",
        name="Water grade",
        value_key="water_grade",
    ),
    ValetudoSensorDescription(
        key="fan_speed",
        name="Fan speed",
        value_key="fan_speed",
    ),
    ValetudoSensorDescription(
        key="segment_count",
        name="Segment count",
        value_key="segment_count",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

CONSUMABLES = (
    ("brush_main", "Main brush remaining"),
    ("brush_side_right", "Side brush remaining"),
    ("filter_main", "Filter remaining"),
    ("cleaning_sensor", "Sensor cleaning remaining"),
    ("cleaning_wheel", "Wheel cleaning remaining"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Valetudo sensors."""
    coordinator: ValetudoCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        ValetudoSensor(coordinator, entry.entry_id, description) for description in SENSORS
    ]
    entities.extend(
        ValetudoConsumableSensor(coordinator, entry.entry_id, key, name) for key, name in CONSUMABLES
    )
    async_add_entities(entities)


class ValetudoSensor(ValetudoRestEntity, SensorEntity):
    """Simple Valetudo sensor."""

    entity_description: ValetudoSensorDescription

    def __init__(
        self,
        coordinator: ValetudoCoordinator,
        entry_id: str,
        description: ValetudoSensorDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.value_key)


class ValetudoConsumableSensor(ValetudoRestEntity, SensorEntity):
    """Valetudo consumable remaining sensor."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: ValetudoCoordinator, entry_id: str, key: str, name: str) -> None:
        super().__init__(coordinator, entry_id)
        self._key = key
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name

    @property
    def native_value(self):
        return self.coordinator.data.get("consumables", {}).get(self._key)
