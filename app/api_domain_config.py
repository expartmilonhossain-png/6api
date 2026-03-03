"""
API Domain Configuration
Manages the active API base URL in a persistent JSON file.
When migrating to a new domain, update this config so apps auto-discover the new URL.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

# Config file lives next to this module
_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "api_domain.json")
_DEFAULT_DOMAIN = "https://api-production-b7c2.up.railway.app"
_ADMIN_PASSWORD_ENV = "ADMIN_PASSWORD"
_ADMIN_PASSWORD_DEFAULT = "apphub2026"


def get_admin_password() -> str:
    return os.getenv(_ADMIN_PASSWORD_ENV, _ADMIN_PASSWORD_DEFAULT)


def get_api_domain() -> str:
    """Read the current API domain from the JSON config file."""
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("apiBaseUrl", _DEFAULT_DOMAIN)
    except Exception as e:
        logger.warning(f"Failed to read api_domain.json: {e}")
    return _DEFAULT_DOMAIN


def set_api_domain(url: str) -> None:
    """Write the new API domain to the JSON config file."""
    url = url.strip().rstrip("/")
    data = {"apiBaseUrl": url}
    with open(_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"✅ API domain updated to: {url}")
