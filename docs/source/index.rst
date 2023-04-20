.. _Actuator-Agent:

==============
Actuator Agent
==============

The Actuator Agent is used to manage write access to devices. Other agents
may request scheduled times, called Tasks, to interact with one or more
devices.

Agents may interact with the ActuatorAgent via either Pub/Sub or RPC,
but RPC is recommended.

The Actuator Agent also triggers the heart beat on devices whose
drivers are configured to do so.

------------

.. _Actuator-Config:

ActuatorAgent Configuration
===========================

The Actuator Agent configuration file accepts the following keys:

:schedule_publish_interval: Interval between schedule state announcements in seconds.
 See `Schedule State Publishes`_. (default: 60)
:preempt_grace_time: Time allowed, in seconds, for a running, preempted Task to clean up,
 before losing access to the device. This applies only to tasks with a priority of
 LOW_PREEMPT. If the Task has no currently open time-slots, it will end immediately.
 (default: 60)
:heartbeat_interval: How often to send a heartbeat signal to all devices in seconds.
 See `Heartbeat Signal`_.  (default: 60)
:driver_vip_identity: The identity of the driver agent for which this actuator agent provides
 scheduling services. (default: "platform.driver")
:allow_no_lock_write: Allow writes to unscheduled devices if there is not a current Task
 managing access to the device. (default: True)

Sample configuration file
-------------------------

.. code-block:: json

    {
        "schedule_publish_interval": 60,
        "preempt_grace_time": 60,
        "heartbeat_interval": 60,
        "driver_vip_identity": "platform.driver",
        "allow_no_lock_write": true
    }


Heartbeat Signal
----------------

The ActuatorAgent can be configured to send a heartbeat message to devices. This indicates to the device that the
platform is running. The ActuatorAgent will set the heartbeat point to alternating "1" and "0" values.
Ideally, if the device recognizes that the heartbeat signal has stopped, it should override actions
taken from VOLTTRON and resume its normal operation. Changes to the heartbeat point will be published like any other
value change on a device.

The configuration has two parts:

* The interval (in seconds) for sending the heartbeat. This is specified with the global `heartbeat_interval` setting.
* The specific point that should be modified each iteration. This is device specific and specified in the driver
  configuration files of individual devices.

----------

.. _Actuator-Communication:

Reserving Device Access through Scheduled Tasks
===============================================

Scheduling a Task
-----------------

.. admonition:: Workflow

    Agents interact with the Actuator Agent following these basic steps:

    #. Schedule a "Task". A Task defines one or more blocks of time during which one or more devices are reserved.
    #. Wait, if needed, until a block of time starts.
    #. Set one or more values on the reserved devices.
    #. Cancel the Task when finished.

Tasks can be scheduled via one of two interfaces:

* The ``request_new_schedule`` RPC method.
* Publishing to the ``devices/actuators/schedule/request`` Pub/Sub topic.

Both methods require four parameters:

:requester_id: The VIP Identity of the requestor. (Required for legacy reasons, but the value is ignored.)
:task_id: A name for the Task.
:priority: :ref:`Priority of the task <Task-Priority>`. Must be either "HIGH", "LOW", or "LOW_PREEMPT"
:requests: The  `Device Schedule`_ --- A list of devices and time ranges for each device.

Device Schedule
^^^^^^^^^^^^^^^

The device schedule is a list of blocks of time reserved for each device.

Both the RPC and Pub/Sub interfaces accept schedules in the following
format. This is the ``requests`` parameter for RPC, and the entire message body
for Pub/Sub:

.. code-block:: python

    [
        ["campus/building/device1",       #First time slot.
         "2013-12-06 16:00:00-00:00",     #Start of time slot.
         "2013-12-06 16:20:00-00:00"],    #End of time slot.
        ["campus/building/device1",       #Second time slot.
         "2013-12-06 18:00:00-00:00",     #Start of time slot.
         "2013-12-06 18:20:00-00:00"],    #End of time slot.
        ["campus/building/device2",       #Third time slot.
         "2013-12-06 16:00:00-00:00",     #Start of time slot.
         "2013-12-06 16:20:00-00:00"],    #End of time slot.
        #etc...
    ]

.. warning::

   If time zones are not included in schedule requests then the Actuator will naively interpret them as being in local time.
   This may cause remote interaction with the actuator to malfunction.

For Pub/Sub requests, the remaining parameters are included in the header, along with
an indication that this is a request for a new schedule:

.. code-block:: python

    {
        "type": "NEW_SCHEDULE",
        "requesterID": <VIP Identity of the requester>
        "taskID": <unique task ID>, #The desired task ID for this task. It must be unique among all other scheduled tasks.
        "priority": <task priority>, #The desired task priority, must be "HIGH", "LOW", or "LOW_PREEMPT"
    }



.. _Task-Priority:

Task Priority
^^^^^^^^^^^^^

There are three valid priority levels:

:HIGH:
    This Task cannot be preempted under any circumstance.
    This Task may preempt other conflicting, preemptable Tasks.
:LOW:
    This Task cannot be preempted **once it has started**.
    A Task is considered started once the earliest time slot on any
    device has been reached. This Task **may not** preempt other Tasks.
:LOW_PREEMPT:
    This Task may be preempted **at any time**.
    If the Task is preempted after it has begun, any current
    time slots will be given a grace period of :ref:`preempt_grace_time <Actuator-Config>`
    seconds to clean up before being revoked. This Task **may not** preempt other Tasks.

Whenever a Task is preempted the Actuator Agent will publish a message to
``devices/actuators/schedule/result`` indicating that the Task has
been cancelled due to being preempted. See `Preemption Publishes`_

Even when using the RPC interface, agents scheduling low priority tasks
should subscribe to ``devices/actuators/schedule/result`` to learn when
Tasks have been canceled due to preemption.

.. admonition:: Points on Task Scheduling

    -  All parameters are required, including those in Pub/Sub headers.
    -  The task and requester IDs should be a non empty strings
    -  The keys in RPC requests are spelled in snake_case, while those in Pub/Sub
       requests are camelCase.
    -  A Task schedule must always have at least one time slot.
    -  The start and end times are parsed with `dateutil's date/time
       parser <http://labix.org/python-dateutil#head-c0e81a473b647dfa787dc11e8c69557ec2c3ecd2>`__.
       The default string representation of a python datetime object will
       parse without issue.
    -  Two Tasks are considered *conflicted* if they contain overlapping
       time slots for the same device.
    -  A request must not *conflict* with itself.
    -  It is not a *conflict* for the end time of one time slot to be the
       same as the start time of another. For example, ``time_slot1(device0, time1, **time2**)`` and
       ``time_slot2(device0, **time2**, time3)`` are not *conflicted*.

New Task Response
^^^^^^^^^^^^^^^^^

Both the RPC and Pub/Sub interface respond to scheduling requests with the following message
(see :ref:`Failure Reasons <Actuator-Failure-Reasons>` for an explanation of
possible errors):

.. code-block:: python

    {
        "result": <"SUCCESS", "FAILURE">,
        "info": <Failure reason string, where appropriate>,
        "data": <Data about the failure / cancellation, where appropriate>
    }

The Pub/Sub interface will respond to requests on the
``devices/actuators/schedule/result`` topic.

Pub/Sub interface responses will have the following header:

.. code-block:: python

    {
        "type": "NEW_SCHEDULE"
        "requesterID": <VIP Identity of requesting agent>,
        "taskID": <Task ID of the request>
    }


Canceling a Task
----------------

Tasks can be canceled via one of two interfaces:

* The ``request_cancel_schedule`` RPC method.
* Publishing to the ``devices/actuators/schedule/request`` Pub/Sub topic.

Both methods require two parameters:

:requester_id: The VIP identity of the agent.
:task_id: The name of the Task.

When using Pub/Sub, only the headers are required. These should be formatted as:

.. code-block:: python

    {
        'type': 'CANCEL_SCHEDULE',
        'requesterID': <Ignored, VIP Identity used internally>
        'taskID': <unique task ID>, #The desired task ID for this task. It must be unique among all other scheduled tasks.
    }


Both the RPC and Pub/Sub interfaces respond to cancellation requests with the
following message (see :ref:`Failure Reasons <Actuator-Failure-Reasons>`
for an explanation of possible errors):

.. code-block:: python

    {
        'result': <'SUCCESS', 'FAILURE'>,
        'info': <Failure reason, if any>,
        'data': {}
    }

The Pub/Sub interface will respond to requests on the ``devices/actuators/schedule/result`` topic
with the following header:

.. code-block:: python

    {
        "type": "CANCEL_SCHEDULE"
        "requesterID": <VIP Identity of requesting agent>,
        "taskID": <Task ID of the request>
    }


.. admonition:: Points on Cancelling Scheduled Tasks

    *  The task ID must match the task ID from the original request.
    *  Attempting to cancel a Task which has already expired will result in a ``TASK_ID_DOES_NOT_EXIST`` error.


---------------------

.. _Actuator-Value-Request:

Actuator Agent Value Requests
=============================

Once an Task has been scheduled and the time slot for one or more of the devices has started,
an agent may interact with the device using the **get**, **set**, and **revert** methods. These
may also be used without a prior reservation if no other agent has scheduled the device
and ``allow_no_lock_write`` is True (the default) in the :ref:`agent configuration <Actuator-Config>`.

Both **get** and **set** methods are responded to in the same manner. See :ref:`Actuator Reply <Actuator-Reply>` below.

Getting values
--------------

While a device driver for a device will periodically poll and publish
the state of a device you may want an up to the moment value for a
point on a device. This can be accomplished using one of several interfaces:

* The ``get_point`` & ``get_multiple_points`` RPC methods.
* Publishing to the ``devices/actuators/get/<full device path>/<actuation point>`` Pub/Sub topic.

The Pub/Sub interface and the ``get_point`` method each return the value
of a single point, while the ``get_multiple_points`` RPC method can,
as its name suggests, return more than point, potentially from multiple devices.

The ``get_point`` RPC method takes two parameters:

:topic: The topic of the device, optionally with the point included.
:point: (optional) The point name, if it was not included in the topic.

.. note::

    The separate specification of the point name is intended to align
    better with the equivalent method on the platform driver, for which
    the point name must always be separate. Following this syntax allows
    agents to optionally work with either the Actuator Agent or directly
    with the Platform Driver.

The ``get_multiple_points`` RPC method takes a single argument:

:topics: Either a list of topics, including point name
 or a list of [topic, point_name] pairs.

The return of ``get_multiple_points`` consists of two dictionaries:

* A dictionary mapping topics (with the point name) to values.
* A dictionary mapping topics (with the point name) to errors.

.. warning::

    As this method does not require that all points return successfully,
    callers should always remember to check the error dictionary.

The Pub/Sub interface does not require a request body nor headers,
since the information regarding device and point are embedded in the topic.

When successful, the ActuatorAgent will respond on the ``devices/actuators/value/<full device path>/<actuation point>``
topic with the message containing the value encoded in JSON. The header will contain:

.. code-block:: python

    {
        'requesterID': <Agent VIP identity>
    }

If there is an error the PUB/SUB interface will publish to the
``devices/actuators/error/<full device path>/<actuation point>`` topic
with the message:

.. code-block:: python

    {
        'type': <Class name of the exception raised by the request>
        'value': <Specific info about the error>
    }


The header will be:

.. code-block:: python

    {
        'requesterID': <VIP Identity of requesting agent>
    }


Setting Values
--------------

The value of points may be set using one of several interfaces:

* The ``set_point`` & ``set_multiple_points`` RPC methods.
* Publishing to the ``devices/actuators/set/<full device path>/<actuation point>`` topic.

These interfaces all pass the request to the the Platform Driver, but only after
performing access control based on the Task schedules and priorities described above.
The Pub/Sub interface and the ``set_point`` method each return the value
of a single point, while the ``set_multiple_points`` RPC method can,
as its name suggests, return more than point, potentially from multiple devices.

Setting a single point by RPC
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``set_point`` RPC method takes three or more parameters:

:requester_id: The VIP identity of the caller. (The actual value is now ignored.)
:topic: The topic of the device, optionally with the point included.
:value: Value to which to set the point.
:point: Point on the device. Uses old behavior if omitted.
:\*\*kwargs: Any driver specific parameters

The return value will be that to which the point was actually set.
Usually invalid values cause an error but some drivers (e.g., Modbus)
will instead return a different value than that which was provided for
setting. An exception will be raised if there is an error setting the point.

Setting multiple points
^^^^^^^^^^^^^^^^^^^^^^^

The ``set_multiple_points`` RPC method can be used to set multiple points
on multiple devices. It makes a single RPC call to the platform driver
for each device. This method takes two or more parameters:

:requester_id: The VIP identity of the caller (The actual value is now ignored.)
:topics_values: A list of (topic, value) tuples.
:\*\*kwargs: Any driver specific parameters.

The return value will be a dictionary mapping points to exceptions raised.
f all points were set successfully an empty dictionary will be returned.

Setting a single point via Pub/Sub
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
When using the Pub/Sub interface, the message body should contain only the value
to which the point is being set. Headers are not required.

When successful, the ActuatorAgent will respond on the ``devices/actuators/value/<full device path>/<actuation point>``
topic with the message containing the value encoded in JSON. The header will contain:

.. code-block:: python

    {
        'requesterID': <Agent VIP identity>
    }

If there is an error the PUB/SUB interface will publish to the
``devices/actuators/error/<full device path>/<actuation point>`` topic
with the message:

.. code-block:: python

    {
        'type': <Class name of the exception raised by the request>
        'value': <Specific info about the error>
    }


The header will be:

.. code-block:: python

    {
        'requesterID': <VIP Identity of requesting agent>
    }


Common Error Types
^^^^^^^^^^^^^^^^^^

    ``LockError``
        Raised when a request is made without permission to
        use a device. (Common causes may include attempting to access a device
        for which another agent owns a scheduled Task, this agent's Task having
        been preempted by another with higher priority, having run out of time
        in the scheduled time slot, etc...)
    ``ValueError``
        Message missing (Pub/Sub only) or has the wrong data type.

Most other error types involve problems with communication between the
VOLTTRON device drivers and the device itself.

Reverting Values and Devices to a Default State
-----------------------------------------------

The value of previously set devices may be reverted to default or prior values.
The exact mechanism used to accomplish this is driver specific. Points may be reverted
using one of four interfaces:

* Single points may be reverted using the ``revert_point`` RPC method or publishing to the
  ``actuators/revert/point/<device path>/<actuation point>`` topic.
* All points on entire devices may be reverted by using the ``revert_device`` RPC method or
  publishing to the ``devices/actuators/revert/device/<device path>`` topic.

For all interfaces, if a different agent has a current, scheduled Task for the device a LockError will be raised.

Reverting Single Points
^^^^^^^^^^^^^^^^^^^^^^^

The ``revert_point`` RPC method reverts the value of a specific point on a device to a default state.
This method requires two or more parameters:

:requester_id: The VIP identity (this value is now ignored).
:topic: The topic of the point to revert in the format, optionally with the point name included.
:point: The point name, if it was not specified in the topic (aligns with the Platform Driver interface).
:\*\*kwargs: Any driver specific parameters.

Alternately, the agent may publish to the ``actuators/revert/point/<device path>/<actuation point>`` topic
with the following header:

.. code-block:: python

        {
            'requesterID': <Ignored, VIP Identity used internally>
        }

The ActuatorAgent will reply on ``devices/actuators/reverted/point/<full device path>/<actuation point>``
to indicate that the point was reverted. Errors will be published on
``devices/actuators/error/<full device path>/<actuation point>``

Reverting Entire Devices
^^^^^^^^^^^^^^^^^^^^^^^^

The ``revert_device`` RPC method reverts all the writable values on a device to a default state.
This method takes at least two parameters:

:requester_id: The VIP Identity of the calling agent (this value is now ignored).
:topic: The topic of the device to revert.
:\*\*kwargs: Any driver specific parameters.

Alternately, the agent may publish to the ``devices/actuators/revert/device/<device path>`` with the fallowing header:

.. code-block:: python

    {
        'requesterID': <Ignored, VIP Identity used internally>
    }

The ActuatorAgent will then reply on the ``devices/actuators/reverted/device/<full device path>`` topic
to indicate that the device was reverted.

Errors will be published on the ``devices/actuators/error/<full device path>/<actuation point>``
topic with the same header as the request.

----------------------

Actuator Feedback Communication
===============================
The Actuator Agent provides several forms of feedback to allow agents to monitor the state of their scheduled Tasks.
This includes notices of preemeption, periodic publishes of state, and meaningful failure codes when requests are not
successful.

Preemption Publishes
--------------------
Both ``LOW`` and ``LOW_PREEMPT`` priority Tasks can be preempted:

* A ``LOW`` priority Task may be preempted by a conflicting ``HIGH`` priority Task *before* it starts.
* A ``LOW_PREEMPT`` priority Task can be preempted a conflicting ``HIGH`` priority Task even *after* it starts.

If a Task is preempted it will publish the following message to the
``devices/actuators/schedule/result`` topic:

.. code-block:: python

    {
        'result': 'PREEMPTED',
        'info': None,
        'data': {
                    'agentID': <Agent ID of preempting task>,
                    'taskID': <Task ID of preempting task>
                }
    }

Along with the following header:

.. code-block:: python

    {
        'type': 'CANCEL_SCHEDULE',
        'requesterID': <VIP ID of the agent which owns the preempted Task>,
        'taskID': <Task ID of the preempted Task>
    }


.. admonition:: Preempt Grace Time

    Remember that if your "LOW_PREEMPT" Task has already started and
    is preempted you have a grace period to do any clean up before
    losing access to the device. The length of this grace period is set
    by ``preempt_grace_time`` in the :ref:`agent configuration <Actuator-Config>`.

.. _Actuator-Schedule-State:

Schedule State Publishes
------------------------

Periodically the ActuatorAgent will publish the state of all currently
reserved devices. The first publish for a device will happen exactly
when the reserved block of time for a device starts.

For each device the ActuatorAgent will publish to an uniquely associated topic:

    ``devices/actuators/schedule/announce/<full device path>``

With the following header:

.. code-block:: python

    {
        'requesterID': <VIP identity of Agent which has access>,
        'taskID': <Task which owns this time slot>
        'window': <Remaining seconds of the time slot>
    }

The frequency of the updates is configurable with the
``schedule_publish_interval`` setting in the :ref:`agent configuration <Actuator-Config>`.


.. _Actuator-Failure-Reasons:

Failure Reasons
---------------

In many cases the Actuator Agent will try to give good feedback as to why
a request failed. Note that some apply only to the Pub/Sub interface.

+--------------------------+-----------------------------------------------------------+
|                              General Failures                                        |
+--------------------------+-----------------------------------------------------------+
|   Failure Code           |  Description                                              |
+==========================+===========================================================+
| **INVALID_REQUEST_TYPE** | Request type was not `NEW_SCHEDULE` or `CANCEL_SCHEDULE`. |
+--------------------------+-----------------------------------------------------------+
| **MISSING_TASK_ID**      | Failed to supply a task ID.                                |
+--------------------------+-----------------------------------------------------------+
| **MISSING_AGENT_ID**     | Agent ID not supplied.                                     |
+--------------------------+-----------------------------------------------------------+

+----------------------------------+---------------------------------------------------+
|Task Scheduling Failures                                                                |
+----------------------------------+---------------------------------------------------+
| Failure Code                     | Description                                       |
+==================================+===================================================+
|TASK_ID_ALREADY_EXISTS            | The supplied task ID already belongs to an existing|
|                                  | task.                                             |
+----------------------------------+---------------------------------------------------+
|MISSING_PRIORITY                  | Failed to supply a priority for a Task schedule   |
|                                  | request.                                          |
+----------------------------------+---------------------------------------------------+
|INVALID_PRIORITY                  | Priority not one of `HIGH`, `LOW`, or             |
|                                  | `LOW_PREEMPT`.                                    |
+----------------------------------+---------------------------------------------------+
|MALFORMED_REQUEST_EMPTY           | Request list is missing or empty.                 |
+----------------------------------+---------------------------------------------------+
|REQUEST_CONFLICTS_WITH_SELF       | Requested time slots on the same device overlap.  |
+----------------------------------+---------------------------------------------------+
|MALFORMED_REQUEST                 | Reported when the request parser raises an        |
|                                  |                                                   |
|                                  | unhandled exception. The exception name and info  |
|                                  |                                                   |
|                                  | are appended to this info string.                 |
+----------------------------------+---------------------------------------------------+
|CONFLICTS_WITH_EXISTING_SCHEDULES | This schedule conflicts with existing schedule(s) |
|                                  |                                                   |
|                                  | that it cannot preempt. The data item for the     |
|                                  |                                                   |
|                                  | results will contain info about the conflicts in  |
|                                  |                                                   |
|                                  | this form:                                        |
|                                  |                                                   |
|                                  | .. code-block:: python                            |
|                                  |                                                   |
|                                  |      {                                            |
|                                  |          "<agentID1>":                            |
|                                  |          {                                        |
|                                  |              "<taskID1>":                         |
|                                  |              [                                    |
|                                  |                  ["campus/building/device1",      |
|                                  |                   "2013-12-06 16:00:00-00:00",    |
|                                  |                   "2013-12-06 16:20:00-00:00"],   |
|                                  |                  ["campus/building/device1",      |
|                                  |                   "2013-12-06 18:00:00-00:00",    |
|                                  |                   "2013-12-06 18:20:00-00:00"]    |
|                                  |              ]                                    |
|                                  |              "<taskID2>":[...]                    |
|                                  |          }                                        |
|                                  |          "<agentID2>": {...}                      |
|                                  |      }                                            |
|                                  |                                                   |
+----------------------------------+---------------------------------------------------+

+-------------------------------+------------------------------------------------------+
| Task Cancellation Failures                                                                 |
+-------------------------------+------------------------------------------------------+
| Failure Code                  | Description                                          |
+===============================+======================================================+
| **TASK_ID_DOES_NOT_EXIST**    | Trying to cancel a Task which does not exist. This   |
|                               |                                                      |
|                               | error can also occur when trying to cancel an already|
|                               |                                                      |
|                               | finished Task.                                       |
+-------------------------------+------------------------------------------------------+
| **AGENT_ID_TASK_ID_MISMATCH** | A different agent ID is being used when trying to    |
|                               |                                                      |
|                               | cancel a Task.                                       |
+-------------------------------+------------------------------------------------------+


.. _Actuator-Notes:

Notes on Working With the ActuatorAgent
=======================================

-  An agent can watch the window value from :ref:`device state updates <Actuator-Schedule-State>` to perform scheduled
   actions within a timeslot

   -  If an Agent's Task is `LOW_PREEMPT` priority it can watch for device state updates where the window is less than
      or equal to the grace period (default 60.0)

-  When considering if to schedule long or multiple short time slots on a single device:

   -  Do we need to ensure the device state for the duration between slots?

       -  Yes: Schedule one long time slot instead
       -  No: Is it all part of the same Task or can we break it up in case there is a conflict with one of our time
          slots?

-  When considering time slots on multiple devices for a single Task:

   -  Is the Task really dependent on all devices or is it actually multiple Tasks?

-  When considering priority:

   -  Does the Task have to happen **on an exact day**?

       -  Yes: Use `HIGH`
       -  No: Consider `LOW` and reschedule if preempted

   -  Is it problematic to prematurely stop a Task once started?

       -  Yes: Consider `LOW` or `HIGH`
       -  No: Consider `LOW_PREEMPT` and watch the device state updates for a small window value

-  If an agent is only observing but needs to assure that no another Task is going on while taking readings it can
   schedule the time to prevent other agents from messing with a devices state.  The schedule updates can be used as a
   reminder as to when to start watching
-  **Any** device, existing or not, can be scheduled.  This allows for agents to schedule fake devices to create
   reminders to start working later rather then setting up their own internal timers and schedules
