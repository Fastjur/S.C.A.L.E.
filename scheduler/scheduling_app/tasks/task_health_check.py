import logging

from scheduler.celery import app as celery_app

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_):
    sender.add_periodic_task(
        10.0,
        task_health_check,
        name="task_health_check",
    )


@celery_app.task
def task_health_check():
    logger.info("If you see this, the task is working fine!")
    return True
