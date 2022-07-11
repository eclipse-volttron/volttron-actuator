"""Tests suite for `volttron_actuator`."""
import json
import pytest

from pathlib import Path

from volttron_actuator.agent import actuator_agent

TESTS_DIR = Path(__file__).parent
TMP_DIR = TESTS_DIR / "tmp"
FIXTURES_DIR = TESTS_DIR / "fixtures"
"""Configuration for the pytest test suite."""


@pytest.fixture()
def actuator():
    config_path = f"{TESTS_DIR}/cfg.json"
    config_json = {
        "schedule_publish_interval": 30,
        "heartbeat_interval": 20,
        "preempt_grace_time": 30
    }

    with open(config_path, 'w') as fp:
        json.dump(config_json, fp)

    yield actuator_agent(config_path)

    Path(config_path).unlink(missing_ok=True)
