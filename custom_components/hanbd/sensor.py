"""Sensor platform for HANBD."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory

from .entity import HanbdEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import HanbdDataUpdateCoordinator
    from .data import HanbdConfigEntry


@dataclass(frozen=True, kw_only=True)
class HanbdSensorEntityDescription(SensorEntityDescription):
    """Describes HANBD sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSOR_DESCRIPTIONS: tuple[HanbdSensorEntityDescription, ...] = (
    HanbdSensorEntityDescription(
        key="active_state",
        name="Status",
        icon="mdi:state-machine",
        value_fn=lambda data: data.get("activeStateName", "unknown"),
    ),
    HanbdSensorEntityDescription(
        key="firmware",
        name="Firmware Version",
        icon="mdi:memory",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("firmware", "unknown"),
    ),
    HanbdSensorEntityDescription(
        key="number1",
        name="Waste Box Level",
        icon="mdi:delete",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("number1"),
    ),
    HanbdSensorEntityDescription(
        key="number2",
        name="Litter Level",
        icon="mdi:gauge",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("number2"),
    ),
    HanbdSensorEntityDescription(
        key="number3",
        name="Uses Today",
        icon="mdi:paw",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("number3"),
    ),
    HanbdSensorEntityDescription(
        key="number4",
        name="Cat Weight",
        icon="mdi:weight-kilogram",
        native_unit_of_measurement="kg",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("number4"),
    ),
    HanbdSensorEntityDescription(
        key="number5",
        name="Number 5",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("number5"),
    ),
    HanbdSensorEntityDescription(
        key="number6",
        name="Number 6",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("number6"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: HanbdConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator

    # Create sensors for each device
    devices = coordinator.data.get("devices", {})

    entities = [
        HanbdSensor(
            coordinator=coordinator,
            device_id=device_id,
            entity_description=description,
        )
        for device_id in devices
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class HanbdSensor(HanbdEntity, SensorEntity):
    """HANBD sensor class."""

    entity_description: HanbdSensorEntityDescription

    def __init__(
        self,
        coordinator: HanbdDataUpdateCoordinator,
        device_id: str,
        entity_description: HanbdSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
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
        self.entity_id = f"sensor.{numeric_id}_{entity_description.key}"

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        return self.entity_description.value_fn(self.device_data)
