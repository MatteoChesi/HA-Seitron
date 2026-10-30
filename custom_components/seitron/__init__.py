"""The Seitron integration."""
from __future__ import annotations

from dataclasses import dataclass

from pyseitron.seitron_gateway import SeitronGateway

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SeitronAuth, SeitronAuthError, SeitronConnectionError
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DOMAIN
from .coordinator import SeitronCoordinator

PLATFORMS: list[Platform] = [Platform.CLIMATE]


@dataclass
class SeitronRuntimeData:
    auth: SeitronAuth
    gateway: SeitronGateway
    coordinator: SeitronCoordinator


SeitronConfigEntry = ConfigEntry  # alias; typed as ConfigEntry[SeitronRuntimeData] when running on HA


async def async_setup_entry(hass: HomeAssistant, entry: SeitronConfigEntry) -> bool:
    """Set up Seitron from a config entry."""
    session = async_get_clientsession(hass)
    auth = SeitronAuth(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    try:
        await auth.async_validate()
    except SeitronAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except SeitronConnectionError as err:
        raise ConfigEntryNotReady(str(err)) from err

    gateway = SeitronGateway(auth)
    coordinator = SeitronCoordinator(hass, auth, gateway)

    await coordinator.async_config_entry_first_refresh()
    if not coordinator.data:
        raise ConfigEntryNotReady("No Seitron devices discovered on this account")

    entry.runtime_data = SeitronRuntimeData(auth, gateway, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SeitronConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
