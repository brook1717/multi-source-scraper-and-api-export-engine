import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from src.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
}


def _is_retryable(exc: BaseException) -> bool:
    """Return True if the exception warrants a retry (429 or 5xx)."""
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        code = exc.response.status_code
        return code == 429 or 500 <= code < 600
    return False


class DataFetcher:
    """HTTP client with automatic retries and error handling."""

    def __init__(self, headers: dict | None = None, timeout: int = DEFAULT_TIMEOUT):
        self.session = requests.Session()
        self.session.headers.update(headers or DEFAULT_HEADERS)
        self.timeout = timeout

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def fetch_data(self, url: str, params: dict | None = None) -> requests.Response:
        """Fetch data from *url* and return the Response.

        Retries up to 3 times with exponential backoff on 429 and 5xx errors.
        Raises on non-retryable HTTP errors and timeouts.
        """
        logger.info("Fetching URL: %s | params: %s", url, params)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            logger.info("Success: %s [%s]", url, response.status_code)
            return response
        except requests.HTTPError as exc:
            logger.warning(
                "HTTP error %s for %s",
                exc.response.status_code if exc.response is not None else "unknown",
                url,
            )
            raise
        except requests.ConnectionError:
            logger.error("Connection error for %s", url)
            raise
        except requests.Timeout:
            logger.error("Request timed out for %s", url)
            raise
        except requests.RequestException as exc:
            logger.error("Unexpected request error for %s: %s", url, exc)
            raise

    def fetch_all_pages(
        self,
        base_url: str,
        params: dict | None = None,
        max_pages: int = 10,
        page_param: str = "page",
        start_page: int = 1,
    ) -> list[dict]:
        """Fetch multiple pages of JSON data and return aggregated results.

        Loops through pages using *page_param* (default 'page') starting at
        *start_page* until the response returns an empty list or *max_pages*
        is reached.
        """
        params = dict(params) if params else {}
        all_results: list[dict] = []

        for page in range(start_page, start_page + max_pages):
            params[page_param] = page
            logger.info("Fetching page %d of %s", page, base_url)

            response = self.fetch_data(base_url, params=params)
            data = response.json()

            # Handle responses that are a list or a dict with a results key
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("results") or data.get("data") or data.get("items") or []
            else:
                items = []

            if not items:
                logger.info("No more data at page %d. Stopping.", page)
                break

            all_results.extend(items)
            logger.info("Page %d returned %d items (total: %d)", page, len(items), len(all_results))

        return all_results
