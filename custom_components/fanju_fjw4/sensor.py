from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import SENSOR_TEMPERATURE, SENSOR_HUMIDITY, DOMAIN
from .coordinator import FanJuCoordinator


def f_to_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0  # як у плагіні  [oai_citation:11‡GitHub](https://raw.githubusercontent.com/slavvka/homebridge-fanju-fjw4/master/src/weather-station.ts)


@dataclass(frozen=True)
class FanJuSensorDesc:
    key: str
    name: str
    sensor_type: int
    channel: int
    device_class: SensorDeviceClass | None
    unit: str | None


SENSORS: list[FanJuSensorDesc] = [
    FanJuSensorDesc("indoor_temp", "Indoor Temperature", SENSOR_TEMPERATURE, 0, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    FanJuSensorDesc("outdoor_temp", "Outdoor Temperature", SENSOR_TEMPERATURE, 1, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    FanJuSensorDesc("indoor_hum", "Indoor Humidity", SENSOR_HUMIDITY, 0, SensorDeviceClass.HUMIDITY, PERCENTAGE),
    FanJuSensorDesc("outdoor_hum", "Outdoor Humidity", SENSOR_HUMIDITY, 1, SensorDeviceClass.HUMIDITY, PERCENTAGE),
]


class FanJuSensor(CoordinatorEntity[FanJuCoordinator], SensorEntity):
    def __init__(self, coordinator: FanJuCoordinator, desc: FanJuSensorDesc) -> None:
        super().__init__(coordinator)
        self.entity_description = None
        self._desc = desc

        dev = (coordinator.data or {}).get("device") or {}
        sn = dev.get("sn") or dev.get("mac") or "fanju_fjw4"

        self._attr_unique_id = f"{sn}_{desc.key}"
        self._attr_name = desc.name
        self._attr_device_class = desc.device_class
        self._attr_native_unit_of_measurement = desc.unit

        self._attr_device_info = {
            "identifiers": {(DOMAIN, sn)},
            "name": dev.get("alias") or "FanJu FJW4",
            "manufacturer": "FanJu",
            "model": "FJW4",
        }

    @property
    def native_value(self) -> float | int | None:
        data: dict[str, Any] = (self.coordinator.data or {}).get("realtime") or {}
        sensor_datas = data.get("sensorDatas") or []

        match = None
        for d in sensor_datas:
            if d.get("type") == self._desc.sensor_type and d.get("channel") == self._desc.channel:
                match = d
                break

        if not match or match.get("curVal") is None:
            return None

        val = match["curVal"]
        if self._desc.sensor_type == SENSOR_TEMPERATURE:
            return round(f_to_c(float(val)), 2)
        return float(val)
