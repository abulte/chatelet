from yaml import safe_load

DEBUG = True
EAGER_QUEUES = False
# Allows domains and subdomains
ALLOWED_DOMAINS = [
    "data.gouv.fr",
    "api.gouv.fr",
    "etalab.studio",
    # for debugging purposes
    "webhook.site",
]
# If set to False, subscriptions are immediately active (dangerous)
VALIDATION_OF_INTENT = True
# deactivate immediate validation of intent
# if VALIDATION_OF_INTENT is True, only delayed validation will be enabled
VALIDATION_OF_INTENT_IMMEDIATE = True

with open("events.yml") as efile:
    EVENTS = safe_load(efile.read())["events"]
