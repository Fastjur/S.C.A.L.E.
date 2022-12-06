import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SchedulingAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scheduling_app"
