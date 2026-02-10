import backoff
import requests


def fatal_code(e):
    # Retry on 429 (rate limit); fail immediately on 4xx client errors
    if e.response.status_code == 429:
        return False
    return 400 <= e.response.status_code < 500


requester = backoff.on_exception(
    backoff.expo,
    (
        requests.exceptions.RequestException,
        requests.exceptions.Timeout,
        TimeoutError,
    ),
    max_time=500,
    giveup=fatal_code,
)
