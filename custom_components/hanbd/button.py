"""Button platform for HANBD."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.exceptions import HomeAssistantError

from .api import HanbdApiClientDeviceBusyError
from .const import LOGGER
from .entity import HanbdEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import HanbdDataUpdateCoordinator
    from .data import HanbdConfigEntry


@dataclass(frozen=True, kw_only=True)
class HanbdButtonEntityDescription(ButtonEntityDescription):
    """Describes HANBD button entity."""

    operation_type: str


BUTTON_DESCRIPTIONS: tuple[HanbdButtonEntityDescription, ...] = (
    HanbdButtonEntityDescription(
        key="clean",
        name="Clean",
        icon="mdi:broom",
        operation_type="CLEAN",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: HanbdConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator = entry.runtime_data.coordinator
    devices = coordinator.data.get("devices", {})
    entities = [
        HanbdButton(
            coordinator=coordinator,
            device_id=device_id,
            entity_description=description,
        )
        for device_id in devices
        for description in BUTTON_DESCRIPTIONS
    ]

    async_add_entities(entities)


class HanbdButton(HanbdEntity, ButtonEntity):
    """HANBD button class."""

    entity_description: HanbdButtonEntityDescription

    def __init__(
        self,
        coordinator: HanbdDataUpdateCoordinator,
        device_id: str,
        entity_description: HanbdButtonEntityDescription,
    ) -> None:
        """Initialize the button entity."""
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
        self.entity_id = f"button.{numeric_id}_{entity_description.key}"

    async def async_press(self) -> None:
        """Handle button press."""
        client = self.coordinator.config_entry.runtime_data.client
        # Try to get the deviceId from various possible field names
        device_api_id = (
            self.device_data.get("deviceId")
            or self.device_data.get("id")
            or self.device_data.get("device_id")
            or self._device_id
        )
        # Convert to string if it's a number
        if device_api_id is not None:
            device_api_id = str(device_api_id)
        else:
            LOGGER.error("No device ID found for device %s", self._device_id)
            return

        try:
            await client.async_operate_device(
                device_id=device_api_id,
                operation_type=self.entity_description.operation_type,
                is_enforce="",
            )
        except HanbdApiClientDeviceBusyError as err:
            # Device is busy, show user-friendly message
            device_name = self.device_data.get("name", self._device_id)
            LOGGER.warning(
                "Cannot %s device '%s': %s",
                self.entity_description.operation_type.lower(),
                device_name,
                err,
            )
            error_msg = (
                f"Device '{device_name}' is currently busy. Please wait and try again."
            )
            raise HomeAssistantError(error_msg) from err

        await self.coordinator.async_request_refresh()
