import random
from config import docker_client


def find_available_port():
    """
    Find an available port in the ephemeral range (49152–65535).
    Ensure the port is not already assigned to any running container.
    """
    while True:
        port = random.randint(49152, 65535)  # Use ephemeral port range
        if not is_port_in_use(port):
            return port

def is_port_in_use(port):
    """
    Check if a specific port is already assigned to a running container.
    """
    try:
        containers = docker_client.containers.list()
        for container in containers:
            ports = container.attrs['HostConfig']['PortBindings']
            if ports:
                for bindings in ports.values():
                    for binding in bindings:
                        if binding['HostPort'] == str(port):
                            return True
        return False
    except Exception as e:
        raise Exception(f"Error checking port usage: {str(e)}")
