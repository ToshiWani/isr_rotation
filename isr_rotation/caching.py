from werkzeug.contrib.cache import SimpleCache


cache = SimpleCache()


def get_cache(key):
    return cache.get(key)


def set_cache(key, value):
    cache.set(key, value, 5 * 60)
    pass

