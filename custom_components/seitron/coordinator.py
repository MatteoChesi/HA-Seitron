"""Data update coordinator for Seitron."""
from __future__ import annotations

import logging

from pyseitron.seitron_gateway import SeitronGateway
from pyseitron.seitron_thermostat import SeitronThermostat

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SeitronAuth, SeitronAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SeitronCoordinator(DataUpdateCoordinator[dict[str, SeitronThermostat]]):
    """Polls the Seitron gateway and exposes devices keyed by gmac."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth: SeitronAuth,
        gateway: SeitronGateway,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.auth = auth
        self.gateway = gateway

    async def _async_update_data(self) -> dict[str, SeitronThermostat]:
        try:
            await self.gateway.update()
        except SeitronAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}") from err
        except Exception as err:  # pyseitron does not define a typed hierarchy
            raise UpdateFailed(f"Error communicating with Seitron: {err}") from err

        return {device.gmac: device for device in self.gateway.devices}
