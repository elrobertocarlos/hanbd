"""Switch platform for HANBD."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from .const import LOGGER
from .entity import HanbdEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import HanbdDataUpdateCoordinator
    from .data import HanbdConfigEntry


@dataclass(frozen=True, kw_only=True)
class HanbdSwitchEntityDescription(SwitchEntityDescription):
    """Describes HANBD switch entity."""

    is_on_fn: Callable[[dict[str, Any]], bool]


SWITCH_DESCRIPTIONS: tuple[HanbdSwitchEntityDescription, ...] = (
    HanbdSwitchEntityDescription(
        key="quiet_mode",
        name="Quiet Mode",
        icon="mdi:volume-off",
        is_on_fn=lambda data: data.get("isQuiet") == 1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: HanbdConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator = entry.runtime_data.coordinator

    # Create switches for each device
    entities = []
    devices = coordinator.data.get("devices", {})

    for device_id in devices:
        entities.extend(
            HanbdSwitch(
                coordinator=coordinator,
                device_id=device_id,
                entity_description=description,
            )
            for description in SWITCH_DESCRIPTIONS
        )

    async_add_entities(entities)


class HanbdSwitch(HanbdEntity, SwitchEntity):
    """HANBD switch class."""

    entity_description: HanbdSwitchEntityDescription

    def __init__(
        self,
        coordinator: HanbdDataUpdateCoordinator,
        device_id: str,
        entity_description: HanbdSwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator, device_id)
        self.entity_description = entity_description
        # Use numeric device ID in unique_id if available, fallback to UDID
        device_data = coordinator.data.get("devices", {}).get(device_id, {})
        numeric_id = device_data.get("id", device_id)
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{numeric_id}_{entity_description.key}"
        )
        self._attr_name = (
            entity_description.name
            if isinstance(entity_description.name, str)
            else None
        )
        # Keep user-facing name clean and enforce deterministic entity_id
        self.entity_id = f"switch.{numeric_id}_{entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.entity_description.is_on_fn(self.device_data)

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        # Control API not yet discovered - quiet mode on/off
        # requires additional endpoint discovery
        LOGGER.warning(
            "Turn on requested for %s/%s but control API not yet implemented",
            self._device_id,
            self.entity_description.key,
        )
        # For now, just refresh to get current state
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        # Control API not yet discovered - quiet mode on/off
        # requires additional endpoint discovery
        LOGGER.warning(
            "Turn off requested for %s/%s but control API not yet implemented",
            self._device_id,
            self.entity_description.key,
        )
        # For now, just refresh to get current state
        await self.coordinator.async_request_refresh()
