from copy import copy
from typing import Dict

from django.http import QueryDict


def prepare_request_data_for_serialization(data: Dict):
    """
    Removes the csrfmiddlewaretoken from `request.data`,
    converts it to a dict if it is a QueryDict
    and returns said new dict.
    """
    request_data_copy = copy(data)
    request_data_copy.pop("csrfmiddlewaretoken", None)
    if isinstance(request_data_copy, QueryDict):
        request_data_copy = request_data_copy.dict()
    return request_data_copy
