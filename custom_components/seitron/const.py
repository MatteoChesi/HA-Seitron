"""Constants for the Seitron integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.climate import HVACAction, HVACMode

DOMAIN = "seitron"

CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_HOST = "https://api.seitron.cloud"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

MIN_TEMP = 5.0
MAX_TEMP = 35.0
TEMP_STEP = 0.5

NO_TARGET_SENTINEL = 3058.3

HVAC_MODE_MAP: dict[str, HVACMode] = {
    "OFF": HVACMode.OFF,
    "HEAT": HVACMode.HEAT,
    "COOL": HVACMode.COOL,
    "AUTO": HVACMode.AUTO,
    "HEAT_COOL": HVACMode.HEAT_COOL,
}

HVAC_MODE_REVERSE_MAP: dict[HVACMode, str] = {v: k for k, v in HVAC_MODE_MAP.items()}

HVAC_ACTION_MAP: dict[str, HVACAction] = {
    "OFF": HVACAction.OFF,
    "IDLE": HVACAction.IDLE,
    "HEATING": HVACAction.HEATING,
    "COOLING": HVACAction.COOLING,
}
