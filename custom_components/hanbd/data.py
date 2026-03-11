"""Custom types for HANBD."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import HanbdApiClient
    from .coordinator import HanbdDataUpdateCoordinator


type HanbdConfigEntry = ConfigEntry[HanbdData]


@dataclass
class HanbdData:
    """Data for the HANBD integration."""

    client: HanbdApiClient
    coordinator: HanbdDataUpdateCoordinator
    integration: Integration
