def get_version(version: tuple) -> str:
    """Return version string (x.y[.z]) from given version tuple.

    :param version: version tuple
    :returns: version string
    """
    parts = 2 if version[2] == 0 else 3
    return '.'.join(str(v) for v in version[:parts])
