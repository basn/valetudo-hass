"""Binary sensors for Valetudo REST."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ValetudoCoordinator
from .entity import ValetudoRestEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Valetudo binary sensors."""
    coordinator: ValetudoCoordinator = entry.runtime_data
    async_add_entities([ValetudoMopAttachedBinarySensor(coordinator, entry.entry_id)])


class ValetudoMopAttachedBinarySensor(ValetudoRestEntity, BinarySensorEntity):
    """Whether the mop is attached."""

    _attr_name = "Mop attached"
    _attr_unique_id = "mop_attached"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: ValetudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_mop_attached"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get("mop_attached")
