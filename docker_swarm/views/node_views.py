# Django Imports
from rest_framework.views import APIView, Response, status
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events
from apscheduler.triggers.interval import IntervalTrigger

# Local Imports
from docker_swarm.utils.node_utils import get_docker_node_detail_info
from docker_swarm.utils.custom_utils import schedule_scale_down
from docker_swarm.utils.scale_up import lunch_template

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")
register_events(scheduler)

if not scheduler.running:
    scheduler.start()


class NodeCollection(APIView):
    def get(self, request):
        node_details = get_docker_node_detail_info()
        if node_details['status'] == 'failed':
            return Response(node_details, status=status.HTTP_400_BAD_REQUEST)
        return Response(node_details)
    
class ScaleUpNodes(APIView):
    def post(self, request, count: int):
        """
        This endpoint will be used to add multiple nodes to the Docker Swarm cluster.
        """
        response = lunch_template(max_count=count)
        return Response({"msg": f"{count} Nodes added to Cluster"}, status=201)


class GetScheduledNodeScaleDown(APIView):
    JOB_ID = "auto-scale-down-scheduler"

    def get(self, request):
        job = scheduler.get_job(self.JOB_ID)

        if not job:
            return Response({"message": "No scheduled job found."})

        if isinstance(job.trigger, IntervalTrigger):
            interval = job.trigger.interval
            trigger_readable = f"Runs every {interval}"
            trigger_details = {
                "type": "interval",
                "interval_seconds": interval.total_seconds()
            }
        else:
            trigger_readable = str(job.trigger)
            trigger_details = {}

        next_run_time = getattr(job, "next_run_time", None)

        return Response({
            "job_id": job.id,
            "job_name": job.name,
            "next_run_time": next_run_time.strftime("%Y-%m-%d %H:%M:%S") if next_run_time else None,
            "trigger": {
                "readable": trigger_readable,
                "details": trigger_details
            }
        })

    def delete(self, request):
        job = scheduler.get_job(self.JOB_ID)
        if job:
            scheduler.remove_job(self.JOB_ID)
            return Response({"message": "Scheduled job deleted successfully."})
        return Response({"message": "No scheduled job found."}, status=status.HTTP_404_NOT_FOUND)

class ScheduleNodeScaleDown(APIView):
    JOB_ID = "auto-scale-down-scheduler"

    def post(self, request, scale_down_schedule_time: int):
        job = scheduler.get_job(self.JOB_ID)
        if job:
            scheduler.remove_job(self.JOB_ID)
        trigger = IntervalTrigger(minutes=int(scale_down_schedule_time))
        scheduler.add_job(
            schedule_scale_down,
            trigger,
            id=self.JOB_ID,
            name=f"Auto scale-down every {scale_down_schedule_time} minutes",
            replace_existing=True,
        )

        return Response({"status": "success", "job_id": self.JOB_ID})
