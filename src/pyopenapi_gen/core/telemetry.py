import os
import time
import json
from typing import Optional, Dict, Any


class TelemetryClient:
    """Opt-in telemetry client, emits events when enabled."""

    def __init__(self, enabled: Optional[bool] = None) -> None:
        if enabled is None:
            env = os.getenv("PYOPENAPI_TELEMETRY_ENABLED", "false").lower()
            self.enabled = env in ("1", "true", "yes")
        else:
            self.enabled = enabled

    def track_event(
        self, event: str, properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track a telemetry event if enabled."""
        if not self.enabled:
            return
        data: Dict[str, Any] = {
            "event": event,
            "properties": properties or {},
            "timestamp": time.time(),
        }
        try:
            # Using print as a stub for actual telemetry transport
            print("TELEMETRY", json.dumps(data))
        except Exception:
            pass
