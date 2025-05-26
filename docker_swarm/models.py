from django.db import models

# Create your models here.

class NodeInstance(models.Model):
    instance_id = models.CharField(max_length=100, unique=True)
    node_id = models.CharField(max_length=100, null=True, blank=True)
    private_ip = models.GenericIPAddressField()
    status = models.CharField(max_length=20, default='provisioning')  # provisioning, active, failed, removed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.instance_id} ({self.status})"


class ScalingState(models.Model):
    key = models.CharField(max_length=100, unique=True, default='global')
    pending_capacity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} - Pending: {self.pending_capacity}"
