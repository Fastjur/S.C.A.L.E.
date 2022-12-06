import functools

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, ValidationError


def generic_error(view_func):
    """Decorator to catch generic error unexpectedly thrown by view func."""

    @functools.wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        drf_exception = None
        base_exception = None

        try:
            return view_func(self, request, *args, **kwargs)
        except ObjectDoesNotExist as err:
            drf_exception = NotFound
            base_exception = err
        except Exception as err:
            drf_exception = ValidationError
            base_exception = err

        if drf_exception:
            raise drf_exception(
                detail={
                    "message": base_exception,
                    "type": type(base_exception).__name__,
                    "query_params": request.query_params,
                    "request_params": request.data,
                },
            )

    return wrapper
