import logging
import sys

from scheduling_app.models import File, Metric, Pod, TaskQueue

logger = logging.getLogger(__name__)


def verify_db_empty():
    if File.objects.all():
        logger.critical(
            "There are Files in the database, "
            "this task requires a clean database to run"
        )
        sys.exit(1)
    if Metric.objects.all():
        logger.critical(
            "There are Metrics in the database, "
            "this task requires a clean database to run"
        )
        sys.exit(1)
    if Pod.objects.all():
        logger.critical(
            "There are Pods in the database, "
            "this task requires a clean database to run"
        )
        sys.exit(1)
    if TaskQueue.objects.all():
        logger.critical(
            "There are TaskQueues in the database, "
            "this task requires a clean database to run"
        )
        sys.exit(1)
