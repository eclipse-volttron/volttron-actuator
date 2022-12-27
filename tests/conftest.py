"""Tests suite for `volttron_actuator`."""
import json
import sys
from pathlib import Path

from actuator.agent import initialize_agent

p = Path(__file__)
if p.parent.parent.parent.resolve().as_posix() not in sys.path:
    sys.path.insert(0, p.parent.parent.resolve().as_posix())

from volttrontesting.fixtures.volttron_platform_fixtures import *

# @pytest.fixture()
# def actuator():
#     config_path = f"{TESTS_DIR}/cfg.json"
#     config_json = {
#         "schedule_publish_interval": 30,
#         "heartbeat_interval": 20,
#         "preempt_grace_time": 30
#     }

    #     with open(config_path, 'w') as fp:
    #         json.dump(config_json, fp)

    #     yield initialize_agent(config_path)

    #     Path(config_path).unlink(missing_ok=True)
