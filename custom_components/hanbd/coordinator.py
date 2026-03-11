"""DataUpdateCoordinator for HANBD."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    HanbdApiClientAuthenticationError,
    HanbdApiClientError,
)
from .const import LOGGER

if TYPE_CHECKING:
    from .data import HanbdConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class HanbdDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: HanbdConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            devices_list = (
                await self.config_entry.runtime_data.client.async_get_devices()
            )

            # Transform list of devices into a dictionary keyed by udid
            devices_dict = {}
            for device in devices_list:
                udid = device.get("udid")
                if udid:
                    devices_dict[udid] = device
                else:
                    LOGGER.warning("Device without udid found: %s", device)

            LOGGER.debug("Fetched %d devices from HANBD API", len(devices_dict))

        except HanbdApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except HanbdApiClientError as exception:
            raise UpdateFailed(exception) from exception
        else:
            return {"devices": devices_dict}
