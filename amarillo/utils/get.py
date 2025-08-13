import requests


def get(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 5,
    user_agent: str = "amarillo +https://github.com/mfdz/amarillo",
):
    request_headers = dict(headers) if headers is not None else {}
    request_headers["User-Agent"] = user_agent
    response = requests.get(url, headers=request_headers, timeout=timeout, params=params)
    response.raise_for_status()
    return response
