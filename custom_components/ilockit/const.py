from datetime import timedelta
from homeassistant.const import Platform

DOMAIN = "ilockit"
DEFAULT_NAME = "ILockit"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

PLATFORMS: list[Platform] = [
    Platform.DEVICE_TRACKER,
]

DEFAULT_SCAN_INTERVAL_SECONDS = 30
DEFAULT_SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)
MIN_SCAN_INTERVAL_SECONDS = 10
MAX_SCAN_INTERVAL_SECONDS = 300
DATA_COORDINATOR = "coordinator"
DATA_API = "api"
