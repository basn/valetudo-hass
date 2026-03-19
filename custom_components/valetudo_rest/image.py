"""Image platform for Valetudo REST."""

from __future__ import annotations

from io import BytesIO
import math

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ValetudoCoordinator
from .entity import ValetudoRestEntity

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    Image = None
    ImageDraw = None


SEGMENT_COLORS = [
    (218, 230, 247),
    (208, 235, 223),
    (248, 229, 202),
    (232, 216, 247),
    (245, 216, 224),
    (222, 235, 235),
    (240, 240, 210),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Valetudo image entity."""
    coordinator: ValetudoCoordinator = entry.runtime_data
    async_add_entities([ValetudoMapImage(coordinator, entry.entry_id)])


class ValetudoMapImage(ValetudoRestEntity, ImageEntity):
    """Rendered Valetudo map image."""

    _attr_name = "Map"
    _attr_content_type = "image/png"
    _attr_should_poll = False

    def __init__(self, coordinator: ValetudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_map"

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return super().available and Image is not None and self.coordinator.data.get("raw_state", {}).get("map") is not None

    async def async_image(self) -> bytes | None:
        """Render the latest Valetudo map as a PNG."""
        if Image is None or ImageDraw is None:
            return None

        state = self.coordinator.data.get("raw_state", {})
        map_data = state.get("map")
        if not map_data:
            return None

        map_size = map_data.get("size", {})
        map_width = int(map_size.get("x", 0))
        map_height = int(map_size.get("y", 0))
        if map_width <= 0 or map_height <= 0:
            return None

        target_width = 768
        scale = max(map_width / target_width, 1)
        render_width = max(1, int(map_width / scale))
        render_height = max(1, int(map_height / scale))

        image = Image.new("RGBA", (render_width, render_height), (248, 249, 250, 255))
        draw = ImageDraw.Draw(image)

        for idx, layer in enumerate(map_data.get("layers", [])):
            if layer.get("type") != "segment":
                continue

            color = SEGMENT_COLORS[idx % len(SEGMENT_COLORS)]
            compressed = layer.get("compressedPixels", [])
            self._draw_runs(draw, compressed, scale, color)

        for entity in map_data.get("entities", []):
            entity_type = entity.get("type")
            points = entity.get("points", [])

            if entity_type == "charger_location" and len(points) >= 2:
                x, y = self._scaled_point(points[0], points[1], scale)
                draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(34, 139, 34, 255))

            elif entity_type == "robot_position" and len(points) >= 2:
                x, y = self._scaled_point(points[0], points[1], scale)
                draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(31, 119, 180, 255))
                angle = entity.get("metaData", {}).get("angle", 0)
                self._draw_heading(draw, x, y, angle)

            elif entity_type == "path" and len(points) >= 4 and len(points) % 2 == 0:
                path = []
                for i in range(0, len(points), 2):
                    path.append(self._scaled_point(points[i], points[i + 1], scale))
                draw.line(path, fill=(120, 120, 120, 255), width=2)

        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    @staticmethod
    def _scaled_point(x: int, y: int, scale: float) -> tuple[int, int]:
        return max(0, int(x / scale)), max(0, int(y / scale))

    @staticmethod
    def _draw_runs(draw: ImageDraw.ImageDraw, compressed: list[int], scale: float, color: tuple[int, int, int]) -> None:
        for i in range(0, len(compressed), 3):
            try:
                x, y, length = compressed[i], compressed[i + 1], compressed[i + 2]
            except IndexError:
                break

            x1 = int(x / scale)
            y1 = int(y / scale)
            x2 = int((x + length) / scale)
            y2 = max(y1 + 1, int((y + 1) / scale))
            draw.rectangle((x1, y1, max(x2, x1 + 1), y2), fill=(*color, 255))

    @staticmethod
    def _draw_heading(draw: ImageDraw.ImageDraw, x: int, y: int, angle_deg: float) -> None:
        radians = math.radians(angle_deg - 90)
        tip_x = x + math.cos(radians) * 18
        tip_y = y + math.sin(radians) * 18
        left_x = x + math.cos(radians + 2.4) * 8
        left_y = y + math.sin(radians + 2.4) * 8
        right_x = x + math.cos(radians - 2.4) * 8
        right_y = y + math.sin(radians - 2.4) * 8
        draw.polygon(
            [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)],
            fill=(17, 24, 39, 255),
        )
