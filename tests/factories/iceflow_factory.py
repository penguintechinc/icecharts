def make_iceflow(overrides=None):
    defaults = {
        "name": "Test IceFlow",
        "description": "A test CI/CD pipeline flow",
        "repository_url": "https://github.com/org/repo",
        "provider": "github",
        "stages": [],
    }
    if overrides:
        defaults.update(overrides)
    return defaults
