def make_playbook(overrides=None):
    defaults = {
        "name": "Test Playbook",
        "description": "A test playbook",
        "nodes": [],
        "edges": [],
        "config": {},
    }
    if overrides:
        defaults.update(overrides)
    return defaults
