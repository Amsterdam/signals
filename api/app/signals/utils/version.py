def get_version(version: tuple = None) -> str:
    """Return version string (x.y[.z]) from given version tuple.

    :param version: version tuple
    :returns: version string
    """
    if version is None:
        from signals import VERSION as version

    parts = 2 if version[2] == 0 else 3
    return '.'.join(str(v) for v in version[:parts])
