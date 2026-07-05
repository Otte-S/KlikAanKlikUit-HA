"""Constants for the KlikAanKlikUit (ICS-2000) integration."""

DOMAIN = "klikaanklikuit"

CONF_TRIES = "tries"
CONF_SLEEP = "sleep"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_LOCAL_IP = "local_ip"

DEFAULT_TRIES = 1
DEFAULT_SLEEP = 3
# scan_interval = seconds between cloud status polls (minimum 5 enforced in
# the options flow). Commands go out over local UDP when the hub IP is known;
# only status reading uses the cloud, since the hardware has no local read.
DEFAULT_SCAN_INTERVAL = 30

MANUFACTURER = "KlikAanKlikUit / Trust"
MODEL_HUB = "ICS-2000"
