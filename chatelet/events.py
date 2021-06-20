import copy
import os
import re

from yaml import safe_load

context = {}


def get_all() -> dict:
    if "events" in context:
        return context["events"]

    with open("events.yml") as efile:
        events = safe_load(efile.read())["events"]

    # replace secret with values
    for _, config in events.items():
        if "secret" in config:
            match = re.match(r"\${(.*)}$", config["secret"])
            if match:
                config["secret"] = os.getenv(match[1])

    context["events"] = events
    return events


def get(event_name: str) -> dict:
    """Map `namespace.xxx.yyy` to the config dict equivalent"""
    events = get_all()
    splitted = event_name.split(".")
    conf_dict = copy.deepcopy(events)
    root = conf_dict.pop(splitted[0], None)
    if not root:
        return None
    _walk = copy.deepcopy(root)
    for idx, part in enumerate(splitted[1:]):
        _walk = _walk.pop(part, None)
        if not _walk and idx != len(splitted):
            return None
    return {
        "event": event_name,
        "secret": root.get("secret", None)
    }
