import os
import json
import time
import sys
import pytest

from pyopenapi_gen.telemetry import TelemetryClient


def test_telemetry_client_default_disabled(monkeypatch, capsys):
    """By default (no env var), telemetry is disabled and track_event prints nothing."""
    env_before = os.environ.pop("PYOPENAPI_TELEMETRY_ENABLED", None)
    tc = TelemetryClient()
    assert not tc.enabled
    # Should not print
    tc.track_event("test_event", {"key": "value"})
    captured = capsys.readouterr()
    assert captured.out == ""
    # Restore env
    if env_before is not None:
        os.environ["PYOPENAPI_TELEMETRY_ENABLED"] = env_before


def test_telemetry_client_enabled_via_env(monkeypatch, capsys):
    """Setting PYOPENAPI_TELEMETRY_ENABLED enables telemetry and prints JSON telemetry data."""
    monkeypatch.setenv("PYOPENAPI_TELEMETRY_ENABLED", "true")
    tc = TelemetryClient()
    assert tc.enabled
    # Capture time to validate timestamp
    start = time.time()
    tc.track_event("my_event", {"foo": 123})
    captured = capsys.readouterr()
    assert captured.out.startswith("TELEMETRY ")
    payload = json.loads(captured.out[len("TELEMETRY ") :])
    assert payload["event"] == "my_event"
    assert payload["properties"] == {"foo": 123}
    # Check timestamp is reasonable
    assert start <= payload["timestamp"] <= time.time()


def test_telemetry_client_enabled_via_constructor(monkeypatch, capsys):
    """Constructor flag enabled=True should override environment and print telemetry."""
    monkeypatch.delenv("PYOPENAPI_TELEMETRY_ENABLED", raising=False)
    tc = TelemetryClient(enabled=True)
    assert tc.enabled
    tc.track_event("evt", None)
    captured = capsys.readouterr()
    assert captured.out.startswith("TELEMETRY ")
    data = json.loads(captured.out.split(None, 1)[1])
    assert data["event"] == "evt"
    assert data["properties"] == {}


def test_track_event_handles_print_exceptions(monkeypatch, capsys):
    """If print/json dumping throws, track_event should catch and not raise."""
    # Simulate enabled
    tc = TelemetryClient(enabled=True)
    # Monkeypatch print to raise
    monkeypatch.setattr(
        "builtins.print",
        lambda *args, **kwargs: (_ for _ in ()).throw(Exception("boom")),
    )
    # Should not propagate
    tc.track_event("e", None)
    # No output since print fails
    captured = capsys.readouterr()
    assert captured.out == ""
