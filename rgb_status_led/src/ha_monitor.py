"""
Home Assistant Status Monitor for RGB Status LED

Monitors Home Assistant for:
- Available updates (core, OS, add-ons)
- Zigbee device health (unavailable entities)
"""

import logging
import os
import re
from typing import Dict, List, Optional
from dataclasses import dataclass

import requests

_LOGGER = logging.getLogger(__name__)

# Supervisor API endpoints
SUPERVISOR_URL = "http://supervisor"

@dataclass
class SystemStatus:
    """System status information."""
    zigbee_issues: bool = False
    updates_available: bool = False
    unavailable_devices: List[str] = None
    pending_updates: List[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.unavailable_devices is None:
            self.unavailable_devices = []
        if self.pending_updates is None:
            self.pending_updates = []


class HAMonitor:
    """Monitors Home Assistant system status."""

    def __init__(
        self,
        check_zigbee: bool = True,
        check_updates: bool = True,
        zigbee_patterns: Optional[List[str]] = None
    ):
        """
        Initialize HA monitor.

        Args:
            check_zigbee: Whether to check for Zigbee device issues
            check_updates: Whether to check for available updates
            zigbee_patterns: List of entity ID patterns to check for Zigbee devices
        """
        self.check_zigbee = check_zigbee
        self.check_updates = check_updates
        self.zigbee_patterns = zigbee_patterns or ["lumi", "zha", "zigbee"]
        self._token = os.environ.get("SUPERVISOR_TOKEN")

        if not self._token:
            _LOGGER.warning("SUPERVISOR_TOKEN not found - API calls will fail")

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    def _api_get(self, endpoint: str) -> Optional[Dict]:
        """
        Make GET request to Supervisor API.

        Args:
            endpoint: API endpoint path

        Returns:
            Response data or None on error
        """
        if not self._token:
            return None

        try:
            url = f"{SUPERVISOR_URL}{endpoint}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json().get("data", {})
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"API request failed for {endpoint}: {e}")
            return None

    def _check_core_updates(self) -> List[str]:
        """Check for Home Assistant Core updates."""
        updates = []

        data = self._api_get("/core/info")
        if data and data.get("update_available"):
            current = data.get("version", "unknown")
            latest = data.get("version_latest", "unknown")
            updates.append(f"Core: {current} -> {latest}")

        return updates

    def _check_os_updates(self) -> List[str]:
        """Check for Home Assistant OS updates."""
        updates = []

        data = self._api_get("/os/info")
        if data and data.get("update_available"):
            current = data.get("version", "unknown")
            latest = data.get("version_latest", "unknown")
            updates.append(f"OS: {current} -> {latest}")

        return updates

    def _check_addon_updates(self) -> List[str]:
        """Check for add-on updates."""
        updates = []

        data = self._api_get("/addons")
        if data:
            addons = data.get("addons", [])
            for addon in addons:
                if addon.get("update_available"):
                    name = addon.get("name", addon.get("slug", "unknown"))
                    updates.append(f"Add-on: {name}")

        return updates

    def _check_supervisor_updates(self) -> List[str]:
        """Check for Supervisor updates."""
        updates = []

        data = self._api_get("/supervisor/info")
        if data and data.get("update_available"):
            current = data.get("version", "unknown")
            latest = data.get("version_latest", "unknown")
            updates.append(f"Supervisor: {current} -> {latest}")

        return updates

    def check_for_updates(self) -> List[str]:
        """
        Check all update sources.

        Returns:
            List of available updates
        """
        if not self.check_updates:
            return []

        all_updates = []
        all_updates.extend(self._check_core_updates())
        all_updates.extend(self._check_os_updates())
        all_updates.extend(self._check_supervisor_updates())
        all_updates.extend(self._check_addon_updates())

        if all_updates:
            _LOGGER.info(f"Found {len(all_updates)} pending updates")
            for update in all_updates:
                _LOGGER.debug(f"  - {update}")

        return all_updates

    def _matches_zigbee_pattern(self, entity_id: str) -> bool:
        """
        Check if entity ID matches Zigbee device patterns.

        Args:
            entity_id: Entity ID to check

        Returns:
            True if entity matches a Zigbee pattern
        """
        entity_lower = entity_id.lower()
        for pattern in self.zigbee_patterns:
            # Support simple wildcards
            if "*" in pattern:
                regex = pattern.replace(".", r"\.").replace("*", ".*")
                if re.match(regex, entity_lower):
                    return True
            elif pattern.lower() in entity_lower:
                return True
        return False

    def check_zigbee_devices(self) -> List[str]:
        """
        Check for unavailable Zigbee devices.

        Only checks cover entities (blinds) to avoid false positives from
        button, number, and other auxiliary entities.

        Returns:
            List of unavailable device entity IDs
        """
        if not self.check_zigbee:
            return []

        unavailable = []

        # Get all entity states via Core API
        try:
            url = f"{SUPERVISOR_URL}/core/api/states"
            response = requests.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            states = response.json()
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Failed to get entity states: {e}")
            return []

        for state in states:
            entity_id = state.get("entity_id", "")
            entity_state = state.get("state", "")

            # Only check cover entities (the actual blinds)
            # Skip buttons, numbers, sensors, and other auxiliary entities
            if not entity_id.startswith("cover."):
                continue

            # Check if this is a Zigbee device
            if self._matches_zigbee_pattern(entity_id):
                # Check if unavailable
                if entity_state == "unavailable":
                    friendly_name = state.get("attributes", {}).get(
                        "friendly_name", entity_id
                    )
                    unavailable.append(friendly_name)
                    _LOGGER.warning(f"Zigbee device unavailable: {friendly_name}")

        if unavailable:
            _LOGGER.info(f"Found {len(unavailable)} unavailable Zigbee devices")

        return unavailable

    def get_status(self) -> SystemStatus:
        """
        Get complete system status.

        Returns:
            SystemStatus object with all status information
        """
        status = SystemStatus()

        try:
            # Check for updates
            status.pending_updates = self.check_for_updates()
            status.updates_available = len(status.pending_updates) > 0

            # Check Zigbee devices
            status.unavailable_devices = self.check_zigbee_devices()
            status.zigbee_issues = len(status.unavailable_devices) > 0

        except Exception as e:
            _LOGGER.error(f"Error getting system status: {e}")
            status.error = str(e)

        return status

    def get_status_priority(self) -> str:
        """
        Get highest priority status for LED display.

        Priority order:
        1. Zigbee issues (red)
        2. Updates available (amber)
        3. All OK (green)

        Returns:
            Status string: 'error', 'updates', or 'ok'
        """
        status = self.get_status()

        if status.zigbee_issues:
            return "error"
        elif status.updates_available:
            return "updates"
        else:
            return "ok"
