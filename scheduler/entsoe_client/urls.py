from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "entsoe"

router = routers.DefaultRouter()
router.register(
    r"solar-wind-forecast",
    views.DayAheadWindAndSolarForecastView,
    basename="solar-wind-forecast",
)
router.register(
    r"actual-generation",
    views.ActualGenerationViewSet,
    basename="actual-generation",
)
router.register(
    r"total-load-forecast",
    views.TotalLoadForecastView,
    basename="total-load-forecast",
)
router.register(
    r"total-load-actual",
    views.TotalLoadActualView,
    basename="total-load-actual",
)
router.register(
    r"renewable-percentage-forecast",
    views.DayAheadRenewablePercentageForecastView,
    basename="renewable-percentage-forecast",
)

urlpatterns = [
    path("", include(router.urls)),
    # path("forecast/", views.forecast, name="forecast"),
    # path("forecast/", views.ForecastView.as_view(), name="forecast"),
]
