import os
import re

from yaml import safe_load

context = {}


def get_all():
    if "events" in context:
        return context["events"]

    with open("events.yml") as efile:
        events = safe_load(efile.read())["events"]

    # replace env vars with values
    for e, config in events.items():
        for k, v in config.items():
            match = re.match(r"\${(.*)}$", v)
            if match:
                config[k] = os.getenv(match[1])

    context["events"] = events
    return events


def get(event_name):
    events = get_all()
    return events.get(event_name)
