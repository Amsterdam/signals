import logging
import os
import re

log = logging.getLogger(__name__)


def get_docker_host():
    """
    Looks for the DOCKER_HOST environment variable to find the VM
    running docker-machine.

    If the environment variable is not found, it is assumed that
    you're running docker on localhost.
    """
    d_host = os.getenv("DOCKER_HOST", None)
    if d_host:
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", d_host):
            return d_host

        return re.match(r"tcp://(.*?):\d+", d_host).group(1)

    return "localhost"


def in_docker():
    """
    Checks pid 1 cgroup settings to check with reasonable certainty we're in a
    docker env.
    :return: true when running in a docker container, false otherwise
    """
    try:
        cgroup = open("/proc/1/cgroup", "r").read()
        return ":/docker/" in cgroup or ":/docker-ce/" in cgroup
    except Exception:
        return False


OVERRIDE_HOST_ENV_VAR = "DATABASE_HOST_OVERRIDE"
OVERRIDE_PORT_ENV_VAR = "DATABASE_PORT_OVERRIDE"


class LocationKey:
    local = "local"
    docker = "docker"
    override = "override"


def get_database_key():
    if os.getenv(OVERRIDE_HOST_ENV_VAR):
        log.warning("Using override database information")
        return LocationKey.override

    elif in_docker():
        log.warning("Using docker database information")
        return LocationKey.docker

    log.warning("Using local database information")
    return LocationKey.local
