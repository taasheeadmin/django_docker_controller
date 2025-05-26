from django.contrib import admin
from docker_swarm.models import NodeInstance, ScalingState

# Register your models here.
admin.site.register([NodeInstance, ScalingState])