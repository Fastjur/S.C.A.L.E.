import logging
from typing import Optional

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from scheduling_app.decorators import generic_error
from scheduling_app.utils import prepare_request_data_for_serialization

logger = logging.getLogger(__name__)


class BaseModelView(APIView):
    """
    Base model view
    All possible configuration:
        - {method}_is_query_set: get_is_query_set or put_is_query_set
        - {method}_serializer: get_serializer or post_serializer
        - response_key: response key to set in the api response
    """

    response_key = None

    def method_serializer(
        self, method: str
    ) -> Optional[serializers.ModelSerializer]:
        """
        Returns method serializer
        Eg:
            post_serializer = FileSerializer
            get_serializer = BatchSerializer
        """
        return getattr(self, f"{method}_serializer".lower(), None)

    def method_is_query_set(self, method: str) -> bool:
        """
        Returns boolean if response is a query set
        Eg:
            get_is_query_set = True
            post_is_query_set = False
        """
        return getattr(self, f"{method}_is_query_set".lower(), False)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Overridden function of DjangoRestFramework
        This function will run after every view function to finalize response
        """

        if type(response) is Response:
            return super().finalize_response(
                request, response, *args, **kwargs
            )

        serializer = self.method_serializer(method=request.method)
        is_query_set = self.method_is_query_set(method=request.method)

        # Serialize response
        if serializer is not None:
            response = serializer(response, many=is_query_set).data

        # Set response key
        if self.response_key is not None and is_query_set is True:
            response = {self.response_key: response}

        response = Response(response)

        return super().finalize_response(request, response, *args, **kwargs)


class BaseSingleModelView(BaseModelView):
    """Base view for single entity get or update"""

    get_is_query_set = False
    patch_is_query_set = False

    url_key = "pk"  # Key used in url to get specific entity
    model = None  # Model class

    prefetch_related = []
    select_related = []

    # Helper functions

    def get_object_by_pk(self, pk):
        query = self.model.objects

        if self.prefetch_related:
            query = query.prefetch_related(*self.prefetch_related)

        if self.select_related:
            query = query.select_related(*self.select_related)

        return query.get(pk=pk)

    # Default generic view functions

    @generic_error
    def get(self, _, *__, **kwargs):
        return self.get_object_by_pk(pk=kwargs[self.url_key])

    @generic_error
    def patch(self, request, *_, **kwargs):
        pk = kwargs[self.url_key]
        # Removing csrfmiddlewaretoken, it is not expected in the serializers
        # Note, this does NOT remove the csrf protection.
        req_data = prepare_request_data_for_serialization(request.data)
        instance = self.model.objects.get(pk=pk)

        # Set attributes
        for attr, value in req_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class BaseQueryPostView(BaseModelView):
    """
    Base Query View used for generic query response
    Query model base on the get parameters
    """

    response_key = "data"
    model = None

    get_is_query_set = True
    post_is_query_set = False

    prefetch_related = []
    select_related = []

    # Default generic view functions

    @generic_error
    def get(self, request):
        logger.debug("GET Request query params: %s", request.query_params)
        _filter = prepare_request_data_for_serialization(request.query_params)

        query = self.model.objects

        if self.prefetch_related:
            query = query.prefetch_related(*self.prefetch_related)

        if self.select_related:
            query = query.select_related(*self.select_related)

        return query.filter(**_filter)

    @generic_error
    def post(self, request):
        logger.debug("[SCHEDULER] POST Request data: %s", request.data)
        # Removing csrfmiddlewaretoken, it is not expected in the serializers
        # Note, this does NOT remove the csrf protection.
        req_data = prepare_request_data_for_serialization(request.data)
        instance = self.model(**req_data)
        instance.save()

        return instance
