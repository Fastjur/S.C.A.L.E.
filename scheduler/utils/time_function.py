import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def time_function(func):
    """
    Decorator to time the execution time of a function, logged to debug
    :param func:
    :return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        wrapped_func_result = func(*args, **kwargs)
        end = time.time()
        elapsed = end - start
        logger.debug(
            "Function %s, time elapsed (s): %s", func.__name__, elapsed
        )

        return wrapped_func_result

    return wrapper


# def metrics(func, timing_model, *args, **kwargs):
#     start = time.time()
#     wrapped_func_result = func(*args, **kwargs)
#     end = time.time()
#     elapsed = end - start
#     logger.debug("Function %s, time elapsed (s): %s", func.__name__, elapsed)
#
#     timing_model.start_time = start
#     timing_model.end_time = end
#     timing_model.save()
#
#     return wrapped_func_result
