"""
Telemetry client for usage tracking and analytics.

This module provides the TelemetryClient class, which handles anonymous
usage telemetry for PyOpenAPI Generator. Telemetry is opt-in only.
"""

import json
import os
import time
from typing import Any


class TelemetryClient:
    """
    Client for sending opt-in telemetry events.

    This class handles emitting usage events to understand how the generator
    is being used. Telemetry is disabled by default and must be explicitly
    enabled either through the PYOPENAPI_TELEMETRY_ENABLED environment
    variable or by passing enabled=True to the constructor.

    Attributes:
        enabled: Whether telemetry is currently enabled
    """

    def __init__(self, enabled: bool | None = None) -> None:
        """
        Initialize a new TelemetryClient.

        Args:
            enabled: Explicitly enable or disable telemetry. If None, the environment
                    variable PYOPENAPI_TELEMETRY_ENABLED is checked.
        """
        if enabled is None:
            env = os.getenv("PYOPENAPI_TELEMETRY_ENABLED", "false").lower()
            self.enabled = env in ("1", "true", "yes")
        else:
            self.enabled = enabled

    def track_event(self, event: str, properties: dict[str, Any] | None = None) -> None:
        """
        Track a telemetry event if telemetry is enabled.

        This method sends a telemetry event with additional properties.
        Events are silently dropped if telemetry is disabled.

        Args:
            event: The name of the event to track
            properties: Optional dictionary of additional properties to include
        """
        if not self.enabled:
            return

        data: dict[str, Any] = {
            "event": event,
            "properties": properties or {},
            "timestamp": time.time(),
        }

        try:
            # Using print as a stub for actual telemetry transport
            # In production, this would be replaced with a proper telemetry client
            print("TELEMETRY", json.dumps(data))
        except Exception as e:
            # Telemetry failures should not affect execution, but log for debugging
            import logging

            logging.getLogger(__name__).debug(f"Telemetry event failed: {e}")
