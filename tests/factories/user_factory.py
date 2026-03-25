def make_user(overrides=None):
    defaults = {
        "email": "user@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "role": "viewer",
    }
    if overrides:
        defaults.update(overrides)
    return defaults


def make_admin(overrides=None):
    return make_user({
        "email": "admin@example.com",
        "role": "admin",
        "full_name": "Admin User",
        **(overrides or {})
    })
