"""
volttron-actuator package.

The Actuator Agent is used to manage write access to devices. Other agents may request scheduled times, called Tasks, to interact with one or more devices.

"""

from typing import List

__all__: List[str] = []    # noqa: WPS410 (the only __variable__ we use)

from volttron.client.messaging.headers import Headers
from volttron.utils import jsonapi


def unpack_legacy_message(headers, message):
    '''Unpack legacy pubsub messages for VIP agents.
    Loads JSON-formatted message parts and removes single-frame messages
    from their containing list. Does not alter headers.
    '''
    if not isinstance(headers, Headers):
        headers = Headers(headers)
    try:
        content_type = headers['Content-Type']
    except KeyError:
        return headers, message
    if isinstance(content_type, str):
        if content_type.lower() == 'application/json':
            if isinstance(message, list) and len(message) == 1:
                return jsonapi.loads(message[0])
            if isinstance(message, str):
                return jsonapi.loads(message)
        if isinstance(message, list) and len(message) == 1:
            return message[0]
    if isinstance(content_type, list) and isinstance(message, list):
        parts = [(jsonapi.loads(msg) if str(ctype).lower() == 'application/json' else msg)
                 for ctype, msg in zip(content_type, message)]
        parts.extend(message[len(parts):])
        if len(parts) == len(content_type) == 1:
            return parts[0]
        return parts
    return message
