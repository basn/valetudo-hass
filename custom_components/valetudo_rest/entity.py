"""Shared entity helpers for Valetudo REST."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ValetudoCoordinator


class ValetudoRestEntity(CoordinatorEntity[ValetudoCoordinator]):
    """Base entity for Valetudo REST."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ValetudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self.coordinator.device_name,
            manufacturer="Valetudo",
            model="Vacuum Robot",
        )


def format_operation_mode(value: str | None) -> str | None:
    """Return a presentation-friendly operation mode string."""
    if not isinstance(value, str):
        return None

    normalized = value.replace("_", " ").replace("-", " ").strip()
    return " ".join(word.capitalize() for word in normalized.split())


def normalize_operation_mode(value: str | None) -> str | None:
    """Return a backend-stable comparable operation mode value."""
    if not isinstance(value, str):
        return None

    return value.replace("_", " ").replace("-", " ").strip().casefold()
