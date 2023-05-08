# volttron-actuator

![Eclipse VOLTTRON 10.0.4rc](https://img.shields.io/badge/Eclipse%20VOLTTRON-10.0.4rc-red.svg)
![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
[![Passing?](https://github.com/eclipse-volttron/volttron-actuator/actions/workflows/run-tests.yml/badge.svg)](https://github.com/VOLTTRON/volttron-actuator/actions/workflows/run-tests.yml)
[![pypi version](https://img.shields.io/pypi/v/volttron-actuator.svg)](https://pypi.org/project/volttron-actuator/)


The Actuator Agent is used to manage write access to devices. Other agents may request scheduled times, called Tasks, to interact with one or more devices.

## Requirements

* python >= 3.10
* volttron >= 10.0
* tzlocal >= 4.2
* types-tzlocal >= 4.2.2.2

## Documentation

More detailed documentation can be found on [ReadTheDocs](https://volttron.readthedocs.io/en/modular/). The RST source
of the documentation for this component is located in the "docs" directory of this repository.

## Installation

Before installing, VOLTTRON should be installed and running.  Its virtual environment should be active.
Information on how to install of the VOLTTRON platform can be found
[here](https://github.com/eclipse-volttron/volttron-core).

Install and start the volttron-actuator.

```shell
vctl install volttron-actuator --agent-config <path to agent config> --start
```

View the status of the installed agent

```shell
vctl status
```

## Development

Please see the following for contributing guidelines [contributing](https://github.com/eclipse-volttron/volttron-core/blob/develop/CONTRIBUTING.md).

Please see the following helpful guide about [developing modular VOLTTRON agents](https://github.com/eclipse-volttron/volttron-core/blob/develop/DEVELOPING_ON_MODULAR.md)

