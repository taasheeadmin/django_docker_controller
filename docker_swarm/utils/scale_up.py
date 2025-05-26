import boto3
from docker_swarm.models import ScalingState, NodeInstance
from django.db import transaction
from docker_swarm.utils.node_utils import get_docker_node_detail_info
from config import *
import time

DEFAULT_KEY = 'global'

def get_pending_capacity():
    try:
        obj, _ = ScalingState.objects.get_or_create(key=DEFAULT_KEY)
        return obj.pending_capacity
    except:
        return 0

@transaction.atomic
def set_pending_capacity(value):
    obj, _ = ScalingState.objects.get_or_create(key=DEFAULT_KEY)
    obj.pending_capacity = value
    obj.save()


def lunch_template(max_count: int = 1):
    # Initialize EC2 client
    ec2 = boto3.client('ec2', aws_access_key_id=access_key, aws_secret_access_key=secret_access_key, region_name=region)

    # Launch an instance using the launch template
    response = ec2.run_instances(
        LaunchTemplate={
            'LaunchTemplateId': launch_template_id,
            'Version': '$Latest'
        },
        MinCount=1,
        MaxCount=max_count
    )
    instance_response = response['Instances'][0]
    instance_id = instance_response['InstanceId']
    ip_address = instance_response['PrivateIpAddress']

    with transaction.atomic():
        NodeInstance.objects.create(instance_id=instance_id, private_ip=ip_address)
        set_pending_capacity(get_pending_capacity() + accepted_containers_count)
    
    return None


def reconcile_swarm_state(node_data):
    """
    Matches EC2 instances to Swarm nodes and resets pending capacity
    when provisioning is complete.
    """
    matched_ips = {node['ip']: node['id'] for node in node_data}

    for node_instance in NodeInstance.objects.filter(status='provisioning'):
        if node_instance.private_ip in matched_ips:
            node_instance.node_id = matched_ips[node_instance.private_ip]
            node_instance.status = 'active'
            node_instance.save()

    if NodeInstance.objects.filter(status='provisioning').exists():
        count = NodeInstance.objects.filter(status='provisioning').count()
        set_pending_capacity(count*accepted_containers_count)
    else:
        set_pending_capacity(0)

    return "Reconciled nodes"


def get_total_available_capacity():
    # Step 1: Get node info
    nodes_response = get_docker_node_detail_info()

    if nodes_response['status'] == 'failed':
        return f"❌ Failed to retrieve node information: {nodes_response.get('error', 'Unknown error')}"

    nodes = nodes_response['data']

    # Step 2: Calculate current + pending capacity
    total_available_capacity = sum(
        max(0, accepted_containers_count - node['tasks_count'])
        for node in nodes
    )

    pending_capacity = get_pending_capacity()
    if pending_capacity > 0 and nodes != []:
        logger.error(reconcile_swarm_state(nodes))

    return total_available_capacity


def check_and_scale_up():
    """
    Checks if the Swarm has enough free capacity for new containers.
    If not, adds a new node to the Swarm and updates pending capacity in DB.

    Returns:
        str: Status message.
    """
    total_available_capacity = get_total_available_capacity()
    pending_capacity = get_pending_capacity()
    effective_capacity = total_available_capacity + pending_capacity

    logger.error(f"Available: {total_available_capacity} | Pending: {pending_capacity} | Effective: {effective_capacity} / Required: {min_capacity_required}")

    # Step 3: Decide whether to scale
    if effective_capacity >= min_capacity_required:
        if total_available_capacity == 0:
            while True:
                total_available_capacity = get_total_available_capacity()
                if total_available_capacity > 0:
                    break
                time.sleep(15)
        return "✅ Sufficient capacity. No scaling needed."

    # Step 4: Trigger scaling logic
    try:
        lunch_template()

        if total_available_capacity == 0:
            while True:
                total_available_capacity = get_total_available_capacity()
                if total_available_capacity > 0:
                    break
                time.sleep(15)

        return f"⚠️ Scaling triggered. Pending capacity now set to {pending_capacity + accepted_containers_count}"
    except Exception as e:
        return f"❌ Scaling failed: {str(e)}"
