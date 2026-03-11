"""HanbdEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import HanbdDataUpdateCoordinator


class HanbdEntity(CoordinatorEntity[HanbdDataUpdateCoordinator]):
    """Base entity class for HANBD devices."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: HanbdDataUpdateCoordinator,
        device_id: str,
    ) -> None:
        """Initialize HANBD entity."""
        super().__init__(coordinator)
        self._device_id = device_id

        # Get device data for creating device_info
        device_data = coordinator.data.get("devices", {}).get(device_id, {})
        # Use numeric device ID in unique_id if available, fallback to UDID
        numeric_id = device_data.get("id", device_id)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{numeric_id}"

        # Build identifiers set with UDID and numeric device ID
        identifiers = {(DOMAIN, device_id)}  # Always include UDID
        # Also include numeric device ID if available
        numeric_id = device_data.get("id")
        if numeric_id:
            identifiers.add((DOMAIN, f"id_{numeric_id}"))

        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            name=device_data.get("name", f"HANBD {device_id}"),
            manufacturer="HANBD",
            model=device_data.get("productCode", "MSP01"),
            sw_version=device_data.get("firmware", "Unknown"),
            hw_version=device_data.get("mac", device_id),
        )

    @property
    def device_data(self) -> dict:
        """Return the device data from coordinator."""
        return self.coordinator.data.get("devices", {}).get(self._device_id, {})
