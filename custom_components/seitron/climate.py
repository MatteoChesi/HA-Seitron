"""Climate platform for the Seitron integration."""
from __future__ import annotations

import logging
from typing import Any

from pyseitron.seitron_thermostat import SeitronThermostat

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SeitronConfigEntry
from .const import (
    DOMAIN,
    HVAC_ACTION_MAP,
    HVAC_MODE_MAP,
    HVAC_MODE_REVERSE_MAP,
    MAX_TEMP,
    MIN_TEMP,
    TEMP_STEP,
)
from .coordinator import SeitronCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SeitronConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up climate entities from a config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        SeitronClimate(coordinator, gmac) for gmac in coordinator.data
    )


class SeitronClimate(CoordinatorEntity[SeitronCoordinator], ClimateEntity):
    """Representation of a Seitron thermostat."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TEMP_STEP
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.AUTO,
    ]

    def __init__(self, coordinator: SeitronCoordinator, gmac: str) -> None:
        super().__init__(coordinator)
        self._gmac = gmac
        self._attr_unique_id = gmac
        device = self._device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, gmac)},
            manufacturer=device.manufacturer,
            name=device.name,
            model=device.model,
            sw_version=device.fw_ver,
        )

    @property
    def _device(self) -> SeitronThermostat:
        return self.coordinator.data[self._gmac]

    @property
    def available(self) -> bool:
        return super().available and self._gmac in self.coordinator.data

    @property
    def current_temperature(self) -> float | None:
        try:
            return self._device.temp_curr
        except AttributeError:
            return None

    @property
    def target_temperature(self) -> float | None:
        try:
            target = self._device.temp_target
        except AttributeError:
            return None
        return target

    @property
    def hvac_mode(self) -> HVACMode | None:
        try:
            raw = self._device.mode
        except AttributeError:
            return None
        if raw is None:
            return None
        mode = HVAC_MODE_MAP.get(str(raw).upper())
        if mode is None:
            _LOGGER.debug("Unknown Seitron mode %r", raw)
        return mode

    @property
    def hvac_action(self) -> HVACAction | None:
        try:
            raw = self._device.hvac_action
        except AttributeError:
            return None
        if raw is None:
            return None
        action = HVAC_ACTION_MAP.get(str(raw).upper())
        if action is None:
            _LOGGER.debug("Unknown Seitron hvac_action %r", raw)
        return action

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.coordinator.gateway.set_temperature(self._gmac, float(temperature))
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        raw = HVAC_MODE_REVERSE_MAP.get(hvac_mode)
        if raw is None:
            _LOGGER.warning("Unsupported HVAC mode %s", hvac_mode)
            return
        await self.coordinator.gateway.set_hvac_mode(self._gmac, raw)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
