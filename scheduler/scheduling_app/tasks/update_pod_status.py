import logging

from django.core.exceptions import ValidationError
from django.utils.timezone import now

from config import settings
from scheduler.celery import app as celery_app
from scheduling_app.models import Pod
from scheduling_app.openshift import get_openshift_client

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_):
    sender.add_periodic_task(
        settings.update_pod_status_interval,
        update_pod_status,
        name="update_pod_status",
    )


@celery_app.task
def update_pod_status():
    logger.info("Updating pod status")
    client = get_openshift_client()

    openshift_pods = client.get_pods()

    # First, clean up all pods that don't exist in openshift anymore
    for pod in Pod.objects.all():
        if pod.status == "deleted":
            continue
        if not any(
            x.name == pod.name and x.namespace == pod.namespace
            for x in openshift_pods
        ):
            logger.info(
                "Found pod %s in database, but not in openshift, deleting "
                "from database",
                pod.name,
            )
            pod.status = "deleted"
            pod.save()

    # Then, update all pods, or create a new one if it does not exist yet.
    for openshift_pod in openshift_pods:
        try:
            pod, _ = Pod.objects.get_or_create(
                pod_identifier=openshift_pod.pod_identifier,
                defaults={
                    "name": openshift_pod.name,
                    "namespace": openshift_pod.namespace,
                    "ip": openshift_pod.ip,
                    "status": openshift_pod.status,
                    "labels": openshift_pod.labels,
                    "created_date": now(),
                    "last_status_update": now(),
                },
            )
            pod.status = openshift_pod.status
            pod.ip = openshift_pod.ip
            pod.last_status_update = now()
            pod.save()
        except ValidationError as err:
            logger.debug(
                "Not creating/updating pod, due to validation error: %s", err
            )
