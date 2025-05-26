import boto3

from docker_swarm.utils.node_utils import get_docker_node_detail_info, get_idle_nodes_to_remove, remove_node_from_swarm
from docker_swarm.models import NodeInstance
from config import logger, access_key, secret_access_key, region

def schedule_scale_down():
    nodes_list_response = get_docker_node_detail_info()

    if nodes_list_response['status'] == 'failed':
        logger.error(nodes_list_response)
        raise Exception(nodes_list_response)
    
    nodes_list = nodes_list_response['data']
    
    idel_node_ids_response = get_idle_nodes_to_remove(nodes_list)
    if idel_node_ids_response['status'] == 'failed':
        logger.error(idel_node_ids_response)
        raise Exception(idel_node_ids_response)
    
    idel_node_ids = idel_node_ids_response['data']
    logger.error("Idle node ID's: ", idel_node_ids)

    if idel_node_ids != []:
        remove_node_from_swarm_response = remove_node_from_swarm(idel_node_ids)

        if remove_node_from_swarm_response['status'] == 'failed':
            logger.error(remove_node_from_swarm_response)
            raise Exception(remove_node_from_swarm_response)
        
        terminate_aws_vm(idel_node_ids)

    return "Done"


def terminate_aws_vm(idel_node_ids):
    logger.error(f"Terminating AWS VMs for idle nodes: {idel_node_ids}")

    instance_ids = list(NodeInstance.objects.filter(node_id__in=idel_node_ids).values_list('instance_id', flat=True))

    # Create an EC2 client
    ec2 = boto3.client('ec2', aws_access_key_id=access_key, aws_secret_access_key=secret_access_key, region_name=region)

    # Terminate the instances
    response = ec2.terminate_instances(InstanceIds=instance_ids)

    NodeInstance.objects.filter(instance_id__in=instance_ids).delete()

    return response
