from enum import Enum
from time import time
from datetime import datetime
from typing import Literal, TypedDict, overload
from urllib.parse import urlencode
from hashlib import sha256
from aiohttp import ClientSession

import hmac
import urllib.request
import json


class API_Call(Enum):
    GET_ROUTES = {
        "endpoint_url": "/api/v3/getroutes",
        "request_type": "getroutes",
    }

    GET_ROUTE_PATTERNS = {
        "endpoint_url": "/api/v3/getpatterns",
        "request_type": "getpatterns",
    }


base_url = "https://riderts.app/bustime"

APIRequestHeader = TypedDict("APIRequestHeader", {"X-Date": str, "X-Request-ID": str})


def build_api_url(
    endpoint_url: str = None,
    request_type: str = None,
    params={},
    xtime: int = None,
    hash_key: str = None,
    api_key: str = None,
) -> tuple[str, APIRequestHeader]:
    if not hash_key:
        raise ValueError("hash_key must be provided")
    if not api_key:
        raise ValueError("api_key must be provided")

    xtime = round(time() * 1000) if xtime is None else xtime
    fmt_time = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    query_params = {
        "requestType": request_type,
        "key": api_key,
        "xtime": xtime,
        "format": "json",
        **params,
    }
    encoded_query_params = urlencode(query_params)

    hash_data = f"{endpoint_url}?{encoded_query_params}{fmt_time}"
    headers: APIRequestHeader = {
        "X-Date": fmt_time,
        "X-Request-ID": hmac.new(
            hash_key.encode("utf-8"), hash_data.encode("utf-8"), sha256
        ).hexdigest(),
    }
    return f"{base_url}/{endpoint_url}?{encoded_query_params}", headers


@overload
def api_call(endpoint_url: str, request_type: str, params={}):
    ...


@overload
def api_call(call_type: Literal[API_Call.GET_ROUTES], params: None = None):
    ...


def base_api_call(
    endpoint_url: str = None,
    request_type: str = None,
    call_type: API_Call = None,
    params={},
    xtime: int = None,
    hash_key: str = None,
    api_key: str = None,
):
    if not hash_key:
        raise ValueError("hash_key must be provided")
    if not api_key:
        raise ValueError("api_key must be provided")

    if call_type:
        endpoint_url = call_type.value["endpoint_url"]
        request_type = call_type.value["request_type"]
    else:
        if not endpoint_url:
            raise Exception("endpoint_url not provided")
        if not request_type:
            raise Exception("request_type not provided")

    return build_api_url(
        endpoint_url, request_type, params, xtime, hash_key=hash_key, api_key=api_key
    )


def api_call(
    endpoint_url: str = None,
    request_type: str = None,
    call_type: API_Call = None,
    params={},
    xtime: int = None,
    hash_key: str = None,
    api_key: str = None,
):
    url, headers = base_api_call(**locals())

    req = urllib.request.Request(
        url,
        headers=headers,
    )
    with urllib.request.urlopen(req) as response:
        res = response.read()
        return json.loads(res)


async def async_api_call(
    session=ClientSession(),
    endpoint_url: str = None,
    request_type: str = None,
    call_type: API_Call = None,
    params={},
    xtime: int = None,
    hash_key: str = None,
    api_key: str = None,
):
    pass_through = {k: v for k, v in locals().items() if k != "session"}

    url, headers = base_api_call(**pass_through)

    async with session.get(url, headers=headers) as resp:
        return await resp.json()
