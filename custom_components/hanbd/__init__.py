"""
Custom integration to integrate HANBD with Home Assistant.

For more details about this integration, please refer to
https://github.com/elrobertocarlos/hanbd
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.loader import async_get_loaded_integration

from .api import HanbdApiClient
from .config_flow import CONF_PHONE
from .const import DOMAIN, LOGGER
from .coordinator import HanbdDataUpdateCoordinator
from .data import HanbdData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import HanbdConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: HanbdConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = HanbdDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(hours=1),
    )
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
    )
    entry.runtime_data = HanbdData(
        client=HanbdApiClient(
            phone=entry.data[CONF_PHONE],
            password=entry.data[CONF_PASSWORD],
            session=session,
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: HanbdConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.async_close()
    return unloaded


async def async_reload_entry(
    hass: HomeAssistant,
    entry: HanbdConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
