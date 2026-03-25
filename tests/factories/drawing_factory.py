def make_drawing(overrides=None):
    defaults = {
        "name": "Test Drawing",
        "description": "A test drawing",
        "content": '{"nodes": [], "edges": []}',
        "is_public": False,
    }
    if overrides:
        defaults.update(overrides)
    return defaults
