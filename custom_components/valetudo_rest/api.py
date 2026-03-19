"""Valetudo REST API client."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientSession


class ValetudoApiError(Exception):
    """Raised on API errors."""


class ValetudoApiClient:
    """Simple Valetudo REST client."""

    def __init__(self, session: ClientSession, host: str) -> None:
        self._session = session
        self._base_url = f"http://{host}/api/v2"

    async def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.request(method, url, json=payload, timeout=15) as response:
                if response.status >= 400:
                    text = await response.text()
                    raise ValetudoApiError(f"{method} {path} failed: {response.status} {text}")

                if response.content_type == "application/json":
                    return await response.json()

                text = await response.text()
                return text or None
        except ValetudoApiError:
            raise
        except (TimeoutError, asyncio.TimeoutError, ClientError, ValueError) as err:
            raise ValetudoApiError(f"{method} {path} failed: {err}") from err

    async def get_state(self) -> dict[str, Any]:
        """Get robot state."""
        return await self._request("GET", "/robot/state")

    async def get_segments(self) -> list[dict[str, Any]]:
        """Get available map segments."""
        return await self._request("GET", "/robot/capabilities/MapSegmentationCapability")

    async def get_segment_properties(self) -> dict[str, Any]:
        """Get map segmentation properties."""
        return await self._request("GET", "/robot/capabilities/MapSegmentationCapability/properties")

    async def get_consumables(self) -> list[dict[str, Any]]:
        """Get consumable states."""
        return await self._request("GET", "/robot/capabilities/ConsumableMonitoringCapability")

    async def get_fan_presets(self) -> list[str]:
        """Get fan presets."""
        return await self._request("GET", "/robot/capabilities/FanSpeedControlCapability/presets")

    async def get_water_presets(self) -> list[str]:
        """Get water presets."""
        return await self._request("GET", "/robot/capabilities/WaterUsageControlCapability/presets")

    async def get_operation_mode_presets(self) -> list[str]:
        """Get operation mode presets."""
        return await self._request("GET", "/robot/capabilities/OperationModeControlCapability/presets")

    async def basic_action(self, action: str) -> None:
        """Send a basic control action."""
        await self._request(
            "PUT",
            "/robot/capabilities/BasicControlCapability",
            {"action": action},
        )

    async def locate(self) -> None:
        """Trigger locate."""
        await self._request("PUT", "/robot/capabilities/LocateCapability")

    async def set_fan_preset(self, name: str) -> None:
        """Set fan speed preset."""
        await self._request(
            "PUT",
            "/robot/capabilities/FanSpeedControlCapability/preset",
            {"name": name},
        )

    async def set_water_preset(self, name: str) -> None:
        """Set water usage preset."""
        await self._request(
            "PUT",
            "/robot/capabilities/WaterUsageControlCapability/preset",
            {"name": name},
        )

    async def set_operation_mode(self, name: str) -> None:
        """Set operation mode preset."""
        await self._request(
            "PUT",
            "/robot/capabilities/OperationModeControlCapability/preset",
            {"name": name},
        )

    async def segment_clean(
        self,
        segment_ids: list[str],
        iterations: int = 1,
        custom_order: bool = True,
    ) -> None:
        """Start a segment clean."""
        await self._request(
            "PUT",
            "/robot/capabilities/MapSegmentationCapability",
            {
                "action": "start_segment_action",
                "segment_ids": segment_ids,
                "iterations": iterations,
                "customOrder": custom_order,
            },
        )

    async def fetch_all(self) -> dict[str, Any]:
        """Fetch the core REST payloads used by entities."""
        (
            state,
            segments,
            segment_properties,
            consumables,
            fan_presets,
            water_presets,
            operation_mode_presets,
        ) = await asyncio.gather(
            self.get_state(),
            self.get_segments(),
            self.get_segment_properties(),
            self.get_consumables(),
            self.get_fan_presets(),
            self.get_water_presets(),
            self.get_operation_mode_presets(),
        )
        return {
            "state": state,
            "segments": segments,
            "segment_properties": segment_properties,
            "consumables": consumables,
            "fan_presets": fan_presets,
            "water_presets": water_presets,
            "operation_mode_presets": operation_mode_presets,
        }
