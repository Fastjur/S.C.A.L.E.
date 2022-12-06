import logging

import requests

from config import settings

logger = logging.getLogger(__name__)


def get_query_url(endpoint, id=None, relationship=None, relationship_id=None):
    query_url = f"{settings.DASHBOARD_BASE_URL}/{endpoint}"

    if id and relationship and relationship_id:
        query_url += f"/{id}/{relationship}/{relationship_id}"

    elif id and relationship:
        query_url += f"/{id}/{relationship}"

    elif id:
        query_url += f"/{id}"

    return query_url


class ApiRequestError(Exception):
    pass


def get_trcs_data(
    endpoint, id=None, relationship=None, relationship_id=None, attributes=None
):
    if attributes is None:
        attributes = {}
    query_url = get_query_url(endpoint, id, relationship, relationship_id)

    logger.info(
        "GET request to TRCS DB: %s, with param %s", query_url, attributes
    )

    headers = {}
    response = requests.get(
        query_url,
        headers=headers,
        params=attributes,
        timeout=settings.REQUESTS_TIMEOUT,
    )

    logger.info("GET request status code: %s", response.status_code)

    # if not 200 <= response.status_code <= 299:
    #     raise requests.HTTPError(
    #         f"Failed to get number of files to untar: {response.text}"
    #     )

    if not _response_is_valid(response):
        unsuccessful_message = (
            f"GET request unsuccessful: {query_url}, "
            f"status_code: {response.status_code}"
        )
        logger.error(unsuccessful_message)
        raise ApiRequestError(unsuccessful_message)

    response_data = response.json()
    logger.info("Response data Received from get TRCS_DB: %s", response_data)

    return response_data


def put_trcs(endpoint, id, data=None):
    if data is None:
        data = {}
    query_url = get_query_url(endpoint, id)

    logger.info("PUT request to TRCS DB: %s, with data:%s", query_url, data)

    headers = {}

    response = requests.put(
        query_url,
        headers=headers,
        timeout=settings.REQUESTS_TIMEOUT,
        json=data.copy(),
    )

    logger.info(f"PUT request status code: {response.status_code}")

    if not _response_is_valid(response):
        unsuccessful_message = (
            f"PUT request unsuccessful: {query_url},"
            f" status_code: {response.status_code}"
        )
        logger.error(unsuccessful_message)
        raise ApiRequestError(unsuccessful_message)

    return None


def patch_trcs(endpoint, id, data=None):
    if data is None:
        data = {}
    query_url = get_query_url(endpoint, id)

    logger.info(f"PATCH request to TRCS DB: {query_url}, with data:{data}")

    headers = {}

    response = requests.patch(
        query_url,
        headers=headers,
        timeout=settings.REQUESTS_TIMEOUT,
        json=data.copy(),
    )

    logger.info(f"PATCH request status code: {response.status_code}")

    if not _response_is_valid(response):
        unsuccessful_message = (
            f"PATCH request unsuccessful: {query_url},"
            f" status_code: {response.status_code}"
        )
        logger.error(unsuccessful_message)
        raise ApiRequestError(unsuccessful_message)

    return None


def post_trcs(endpoint, data=None):
    if data is None:
        data = {}
    query_url = get_query_url(endpoint)
    logger.info("POST request to TRCS DB: %s, with data: %s", query_url, data)

    headers = {}
    response = requests.post(
        query_url,
        headers=headers,
        timeout=settings.REQUESTS_TIMEOUT,
        json=data.copy(),
    )

    logger.info("POST request status code: %s", response.status_code)

    if not _response_is_valid(response):
        unsuccessful_message = (
            f"POST request unsuccessful: {query_url}, "
            f"status_code: {response.status_code}, "
            f"response: {response.text}"
        )
        logger.error(unsuccessful_message)
        raise ApiRequestError(unsuccessful_message)

    response_data = response.json()
    logger.info("Response data Received from post TRCS_DB: %s", response_data)

    return response_data


def _response_is_valid(response):
    return 200 <= response.status_code <= 299
