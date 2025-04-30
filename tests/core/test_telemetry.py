import json
import os
from typing import Any

from pyopenapi_gen.core.telemetry import TelemetryClient


def test_telemetry_default_disabled(capsys: Any) -> None:
    """By default, telemetry should be disabled and produce no output."""
    # Ensure no env var set
    os.environ.pop("PYOPENAPI_TELEMETRY_ENABLED", None)
    client = TelemetryClient()
    client.track_event("test_event", {"key": "value"})
    captured = capsys.readouterr()
    assert captured.out == ""


def test_telemetry_enabled_env_var(capsys: Any, monkeypatch: Any) -> None:
    """When env var is set to true, telemetry prints event."""
    monkeypatch.setenv("PYOPENAPI_TELEMETRY_ENABLED", "true")
    client = TelemetryClient()
    client.track_event("evt", {"a": 1})
    captured = capsys.readouterr()
    out = captured.out.strip()
    # Should start with TELEMETRY and valid JSON
    assert out.startswith("TELEMETRY ")
    _, payload = out.split(" ", 1)
    data = json.loads(payload)
    assert data["event"] == "evt"
    assert data["properties"]["a"] == 1
    assert "timestamp" in data


def test_telemetry_enabled_parameter(capsys: Any) -> None:
    """When enabled=True passed, telemetry prints event regardless of env."""
    os.environ.pop("PYOPENAPI_TELEMETRY_ENABLED", None)
    client = TelemetryClient(enabled=True)
    client.track_event("param_evt", None)
    captured = capsys.readouterr()
    out = captured.out.strip()
    assert out.startswith("TELEMETRY ")
    _, payload = out.split(" ", 1)
    data = json.loads(payload)
    assert data["event"] == "param_evt"
    assert data["properties"] == {}


def test_telemetry_disabled_parameter(capsys: Any) -> None:
    """When enabled=False passed, telemetry produces no output regardless of env."""
    monkey_env = os.environ.get("PYOPENAPI_TELEMETRY_ENABLED")
    os.environ["PYOPENAPI_TELEMETRY_ENABLED"] = "true"
    client = TelemetryClient(enabled=False)
    client.track_event("no_evt", {})
    captured = capsys.readouterr()
    assert captured.out == ""
    # restore env
    if monkey_env is not None:
        os.environ["PYOPENAPI_TELEMETRY_ENABLED"] = monkey_env
    else:
        os.environ.pop("PYOPENAPI_TELEMETRY_ENABLED")
