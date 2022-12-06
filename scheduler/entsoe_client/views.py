import logging

import arrow
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from entsoe_client import get_entsoe_api_client
from entsoe_client.models import (
    ActualGenerationPerProductionTypeDataSerializer,
    DayAheadTotalLoadForecastDataSerializer,
    DayAheadWindAndSolarDataSerializer,
    ActualTotalLoadDataSerializer,
    DayAheadRenewablePercentageForecastDataSerializer,
)
from entsoe_service import EntsoeService

logger = logging.getLogger(__name__)


def index(_):
    return JsonResponse(
        {"message": "Hello, world. You're at the entsoe_client index."}
    )


class DayAheadWindAndSolarForecastView(viewsets.ViewSet):
    serializer_class = DayAheadWindAndSolarDataSerializer

    @staticmethod
    def list(request):
        start_date = arrow.get(
            request.query_params.get("start_date"), tzinfo="Europe/Amsterdam"
        )
        end_date = arrow.get(
            request.query_params.get("end_date"), tzinfo="Europe/Amsterdam"
        )

        if start_date is None or end_date is None:
            return HttpResponseBadRequest(
                "start_date and end_date are required parameters."
            )

        entsoe_api_client = get_entsoe_api_client()

        day_ahead_forecast = entsoe_api_client.get_wind_solar_day_ahead(
            start_date=start_date, end_date=end_date
        )
        serializer = DayAheadWindAndSolarDataSerializer(
            instance=day_ahead_forecast,
        )
        return Response(serializer.data)


class ActualGenerationViewSet(viewsets.ViewSet):
    serializer_class = ActualGenerationPerProductionTypeDataSerializer

    @staticmethod
    def list(request):
        start_date = arrow.get(
            request.query_params.get("start_date"), tzinfo="Europe/Amsterdam"
        )
        end_date = arrow.get(
            request.query_params.get("end_date"), tzinfo="Europe/Amsterdam"
        )

        if start_date is None or end_date is None:
            return HttpResponseBadRequest(
                "start_date and end_date are required parameters."
            )

        entsoe_api_client = get_entsoe_api_client()
        actual_generation = entsoe_api_client.get_actual_generation_per_type(
            start_date=start_date.floor("day"),
            end_date=end_date.shift(days=1).floor("day"),
        )
        serializer = ActualGenerationPerProductionTypeDataSerializer(
            instance=actual_generation,
        )
        return Response(serializer.data)


class TotalLoadForecastView(ViewSet):
    serializer_class = DayAheadTotalLoadForecastDataSerializer

    @staticmethod
    def list(request):
        start_date = arrow.get(
            request.query_params.get("start_date"), tzinfo="Europe/Amsterdam"
        )
        end_date = arrow.get(
            request.query_params.get("end_date"), tzinfo="Europe/Amsterdam"
        )

        if start_date is None or end_date is None:
            return HttpResponseBadRequest(
                "start_date and end_date are required parameters."
            )

        entsoe_api_client = get_entsoe_api_client()
        total_load_forecast = entsoe_api_client.get_total_load_forecast(
            start_date=start_date, end_date=end_date
        )
        serializer = DayAheadTotalLoadForecastDataSerializer(
            instance=total_load_forecast,
        )
        return Response(serializer.data)


class TotalLoadActualView(ViewSet):
    serializer_class = ActualTotalLoadDataSerializer

    @staticmethod
    def list(request):
        start_date = arrow.get(
            request.query_params.get("start_date"), tzinfo="Europe/Amsterdam"
        )
        end_date = arrow.get(
            request.query_params.get("end_date"), tzinfo="Europe/Amsterdam"
        )

        if start_date is None or end_date is None:
            return HttpResponseBadRequest(
                "start_date and end_date are required parameters."
            )

        entsoe_api_client = get_entsoe_api_client()
        actual_load_realised = entsoe_api_client.get_actual_load_realised(
            start_date=start_date, end_date=end_date.shift(days=1).floor("day")
        )
        serializer = ActualTotalLoadDataSerializer(
            instance=actual_load_realised,
        )
        return Response(serializer.data)


class DayAheadRenewablePercentageForecastView(ViewSet):
    @staticmethod
    def list(request):
        start_date = arrow.get(
            request.query_params.get("start_date"), tzinfo="Europe/Amsterdam"
        )
        end_date = arrow.get(
            request.query_params.get("end_date"), tzinfo="Europe/Amsterdam"
        )

        if start_date is None or end_date is None:
            return HttpResponseBadRequest(
                "start_date and end_date are required parameters."
            )

        entsoe_service = EntsoeService(get_entsoe_api_client())
        renewable_percentage_forecast = (
            entsoe_service.get_renewable_percentage_forecast(
                start_date=start_date, end_date=end_date
            )
        )
        serializer = DayAheadRenewablePercentageForecastDataSerializer(
            instance=renewable_percentage_forecast
        )
        return Response(serializer.data)
