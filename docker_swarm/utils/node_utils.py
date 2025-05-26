from config import docker_client, accepted_containers_count, min_capacity_required, logger
from docker_swarm.models import NodeInstance
import docker

def get_docker_node_detail_info():
    """
    Fetch Docker Swarm worker node info and list of running tasks on each node.
    """
    try:
        api_client = docker.APIClient(base_url='unix://var/run/docker.sock')
        node_detail_list = []

        try:
            nodes = docker_client.nodes.list()
        except docker.errors.APIError as e:
            if "This node is not a swarm manager" in str(e):
                msg = "Docker is not running in Swarm mode."
                return {'status': 'failed', 'error': msg}
            else:
                msg = f"Error checking Swarm status: {e}"
                return {'status': 'failed', 'error': msg}

        for node in nodes:
            if node.attrs['Spec']['Role'] != 'worker':
                continue  # Skip managers

            node_id = node.attrs.get('ID')

            tasks = api_client.tasks(filters={'node': node_id, 'desired-state': ['running']})
            task_info = []
            for task in tasks:
                container_spec = task.get('Spec', {}).get('ContainerSpec', {})
                # for key, value in task.items():
                #     logger.error(key, value)
                task_info.append({
                    'id': task.get('ID'),
                    'name': container_spec['Mounts'][0]['Source'].split("/")[-1],
                    'image': container_spec.get('Image'),
                    'State': task['Status']['State'],
                })

            node_detail_list.append({
                'id': node.attrs.get('ID'),
                'availability': node.attrs['Spec']['Availability'],
                'hostname': node.attrs['Description']['Hostname'],
                'ip': node.attrs.get('Status', {}).get('Addr', 'N/A'),
                'status': node.attrs.get('Status', {}).get('State', 'N/A'),
                'tasks_count': len(task_info),
                'tasks': task_info
            })

        return {'status': 'success', 'data': node_detail_list}

    except docker.errors.DockerException as e:
        msg = f"An error occurred: {e}"
        return {'status': 'failed', 'error': msg}

def get_idle_nodes_to_remove(nodes: list):
    """
    Returns a list of idle node IDs that can be removed,
    only if the rest of the cluster can handle their potential container load.

    Args:
        nodes (list): List of node details with 'tasks_count'.
        accepted_containers_count (int): Max containers per node.
        min_capacity_required (int): Minimum buffer space to preserve (per idle node removed).

    Returns:
        List of idle node IDs that can be safely removed.
    """
    try:
        idle_nodes = [node for node in nodes if node['tasks_count'] == 0]
        active_nodes = [node for node in nodes if node['tasks_count'] > 0]

        # Start with total available capacity from active nodes
        total_available_capacity = sum(
            max(0, accepted_containers_count - node['tasks_count'])
            for node in active_nodes
        )

        removable_idle_nodes = []

        # If all nodes are idle, keep one to serve as future container host
        if not active_nodes and len(idle_nodes) > 1:
            idle_to_keep = idle_nodes[0]  # Keep first idle node
            logger.error(f"Keeping idle node '{idle_to_keep['id']}' as backup.")
            total_available_capacity += accepted_containers_count
            idle_nodes = idle_nodes[1:]  # Others can be considered for removal

        # Check if we can safely remove idle nodes
        for node in idle_nodes:
            if total_available_capacity >= min_capacity_required:
                removable_idle_nodes.append(node['id'])
                total_available_capacity -= min_capacity_required
            else:
                break

        return {'status': 'success', 'data': removable_idle_nodes}
    except Exception as error:
        return {'status': 'failed', 'error': str(error)}

def remove_node_from_swarm(node_ids_list, force=True):
    """
    Removes a node from Docker Swarm.

    Args:
        node_id (str): Node ID or hostname.
        force (bool): Whether to force the removal.

    Returns:
        dict: Status and optional error message.
    """
    for node_id in node_ids_list:
        try:
            client = docker.from_env()
            node = client.nodes.get(node_id)
            node.remove(force=force)
            logger.error(f"Node '{node_id}' removed successfully.")
            node_db = NodeInstance.objects.get(node_id=node_id)
            node_db.status = "removed"
            node_db.save()

        except docker.errors.NotFound:
            return {'status': 'failed', 'error': f"Node '{node_id}' not found."}
        except docker.errors.APIError as e:
            return {'status': 'failed', 'error': f"Docker API error: {e}"}
        except docker.errors.DockerException as e:
            return {'status': 'failed', 'error': f"Docker error: {e}"}
        except Exception as e:
            return {'status': 'failed', 'error': f"Unexpected error: {e}"}
    return {'status': 'success'}
