from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FanJuCoordinator
from .const import DOMAIN, SENSOR_TEMPERATURE, SENSOR_HUMIDITY


def f_to_c(value: float) -> float:
    return round((value - 32.0) * 5.0 / 9.0, 2)


@dataclass(frozen=True)
class FanJuSensorDescription(SensorEntityDescription):
    sensor_type: int = 0
    channel: int = 0


SENSOR_DESCRIPTIONS: tuple[FanJuSensorDescription, ...] = (
    FanJuSensorDescription(
        key="indoor_temperature",
        name="Indoor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        sensor_type=SENSOR_TEMPERATURE,
        channel=0,
    ),
    FanJuSensorDescription(
        key="outdoor_temperature",
        name="Outdoor Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        sensor_type=SENSOR_TEMPERATURE,
        channel=1,
    ),
    FanJuSensorDescription(
        key="indoor_humidity",
        name="Indoor Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        sensor_type=SENSOR_HUMIDITY,
        channel=0,
    ),
    FanJuSensorDescription(
        key="outdoor_humidity",
        name="Outdoor Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        sensor_type=SENSOR_HUMIDITY,
        channel=1,
    ),
)


class FanJuSensor(CoordinatorEntity[FanJuCoordinator], SensorEntity):
    entity_description: FanJuSensorDescription

    def __init__(
        self,
        coordinator: FanJuCoordinator,
        description: FanJuSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        device = coordinator.device or {}
        sn = device.get("sn") or device.get("mac") or "fanju_fjw4"

        self._attr_unique_id = f"{sn}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, sn)},
            "name": device.get("alias") or "FanJu FJW4",
            "manufacturer": "FanJu",
            "model": "FJW4",
        }

    @property
    def native_value(self) -> float | int | None:
        data: dict[str, Any] = (self.coordinator.data or {}).get("realtime") or {}
        sensor_datas = data.get("sensorDatas") or []

        for item in sensor_datas:
            if (
                item.get("type") == self.entity_description.sensor_type
                and item.get("channel") == self.entity_description.channel
            ):
                value = item.get("curVal")
                if value is None:
                    return None

                if self.entity_description.sensor_type == SENSOR_TEMPERATURE:
                    return f_to_c(float(value))

                return float(value)

        return None


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator: FanJuCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        FanJuSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )
