from django.urls import path
from docker_swarm.views import docker_views, node_views

urlpatterns = []

docker_urls = [
    path('task', docker_views.ContainerCollection.as_view(), name='task_collection'),
    path('task/<username>', docker_views.ContainerResource.as_view(), name='task_resource')
]
urlpatterns.extend(docker_urls)

node_urls = [
    path('node', node_views.NodeCollection.as_view(), name='node_list'),
    path('node/<int:count>', node_views.ScaleUpNodes.as_view(), name='scale_up_nodes'),
    path('schedule_autoscaledown', node_views.GetScheduledNodeScaleDown.as_view(), name='schedule_autoscaledown'),
    path('schedule_autoscaledown/<int:scale_down_schedule_time>', node_views.ScheduleNodeScaleDown.as_view(), name='schedule_autoscaledown'),
]
urlpatterns.extend(node_urls)
