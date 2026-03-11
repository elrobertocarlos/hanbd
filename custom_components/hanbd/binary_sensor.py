"""Binary sensor platform for HANBD."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.typing import UNDEFINED

from .entity import HanbdEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import HanbdDataUpdateCoordinator
    from .data import HanbdConfigEntry


@dataclass(frozen=True, kw_only=True)
class HanbdBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes HANBD binary sensor entity."""

    is_on_fn: Callable[[dict[str, Any]], bool]


BINARY_SENSOR_DESCRIPTIONS: tuple[HanbdBinarySensorEntityDescription, ...] = (
    HanbdBinarySensorEntityDescription(
        key="online",
        name="Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data: data.get("isOnline") == 1,
    ),
    HanbdBinarySensorEntityDescription(
        key="roller_full",
        name="Roller Full",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:delete-alert",
        is_on_fn=lambda data: data.get("isRollerFull") == 1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: HanbdConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    coordinator = entry.runtime_data.coordinator

    # Create binary sensors for each device
    entities = []
    devices = coordinator.data.get("devices", {})

    for device_id in devices:
        entities.extend(
            HanbdBinarySensor(
                coordinator=coordinator,
                device_id=device_id,
                entity_description=description,
            )
            for description in BINARY_SENSOR_DESCRIPTIONS
        )

    async_add_entities(entities)


class HanbdBinarySensor(HanbdEntity, BinarySensorEntity):
    """HANBD binary_sensor class."""

    entity_description: HanbdBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: HanbdDataUpdateCoordinator,
        device_id: str,
        entity_description: HanbdBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator, device_id)
        self.entity_description = entity_description
        # Use numeric device ID in unique_id if available, fallback to UDID
        device_data = coordinator.data.get("devices", {}).get(device_id, {})
        numeric_id = device_data.get("id", device_id)
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{numeric_id}_{entity_description.key}"
        )
        self._attr_name = (
            None if entity_description.name is UNDEFINED else entity_description.name
        )
        # Keep user-facing name clean and enforce deterministic entity_id
        self.entity_id = f"binary_sensor.{numeric_id}_{entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return self.entity_description.is_on_fn(self.device_data)
