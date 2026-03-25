def make_icerun(overrides=None):
    defaults = {
        "name": "Test IceRun",
        "description": "A test serverless function",
        "runtime": "python3.13",
        "handler": "main.handler",
        "entrypoint": "main.py",
        "config": {},
    }
    if overrides:
        defaults.update(overrides)
    return defaults
