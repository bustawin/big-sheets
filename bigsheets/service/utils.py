import decouple


def debug():
    return decouple.config("DEBUG", default=False, cast=bool)
