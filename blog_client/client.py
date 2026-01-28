from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any
import requests
from pydantic import ValidationError
from blog_client.models import Comment, CommentsAdapter, Post, PostsAdapter

class APIClientError(Exception):
    """Базовая ошибка клиента (понятная для пользователя)."""

class APIClientHTTPError(APIClientError):
    """HTTP-ошибка (4xx/5xx), которую мы хотим показать пользователю."""

class APIClientNetworkError(APIClientError):
    """Сетевая ошибка (timeout, проблемы соединения и т.п.)."""

@dataclass(frozen=True)
class RetryConfig:
    attempts: int = 3
    backoff_seconds: tuple[float, ...] = (0.5, 1.0, 2.0)
    retry_statuses: tuple[int, ...] = (500, 502, 503, 504)

class APIClient:
    def __init__(
        self,
        base_url: str = "https://jsonplaceholder.typicode.com",
        timeout: float | tuple[float, float] = 10.0,
        headers: dict[str, str] | None = None,
        retry: RetryConfig = RetryConfig(),
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry = retry
        self.session = requests.Session()

        if headers:
            self.session.headers.update(headers)

    def close(self) -> None:
        self.session.close()

    def _full_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """
        Делает HTTP-запрос и возвращает requests.Response (без попытки парсить JSON).
        Тут же: таймауты, ретраи, обработка кодов, логирование.
        """
        url = self._full_url(path)
        last_exc: Exception | None = None

        for attempt in range(1, self.retry.attempts + 1):
            t0 = time.perf_counter()
            resp: requests.Response | None = None

            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=self.timeout,
                )

                dt_ms = (time.perf_counter() - t0) * 1000
                print(f"[HTTP] {method.upper()} {url} -> {resp.status_code} ({dt_ms:.0f} ms)")

                if 200 <= resp.status_code < 300:
                    return resp

                if 400 <= resp.status_code < 500:
                    raise APIClientHTTPError(f"HTTP {resp.status_code}: {url}")

                if resp.status_code in self.retry.retry_statuses:
                    raise APIClientHTTPError(f"HTTP {resp.status_code} (retryable): {url}")

                raise APIClientHTTPError(f"HTTP {resp.status_code}: {url}")

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exc = e
                dt_ms = (time.perf_counter() - t0) * 1000
                print(
                    f"[HTTP] {method.upper()} {url} -> NETWORK ERROR ({dt_ms:.0f} ms): {type(e).__name__}"
                )

            except APIClientHTTPError as e:
                last_exc = e

                if resp is not None and 400 <= resp.status_code < 500:
                    raise

                if attempt < self.retry.attempts:
                    backoff = self.retry.backoff_seconds[
                        min(attempt - 1, len(self.retry.backoff_seconds) - 1)
                    ]
                    time.sleep(backoff)
                else:
                    break

        if isinstance(last_exc, APIClientError):
            raise last_exc

        raise APIClientNetworkError(f"Не удалось выполнить запрос: {url}") from last_exc

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Делает HTTP-запрос и возвращает Python-объект из response.json().
        """
        resp = self.request(method, path, params=params)
        try:
            return resp.json()
        except ValueError as e:
            raise APIClientError(f"Ответ не JSON: {resp.url}") from e

    def get_posts_page(self, *, limit: int, start: int) -> list[Post]:
        data = self.request_json(
            "GET",
            "/posts",
            params={"_limit": limit, "_start": start},
        )
        try:
            return PostsAdapter.validate_python(data)
        except ValidationError as e:
            raise APIClientError("Ответ /posts имеет неожиданную структуру") from e

    def iter_all_posts(self, *, limit: int) -> "list[Post]":
        start = 0
        while True:
            page = self.get_posts_page(limit=limit, start=start)
            if not page:
                break
            for post in page:
                yield post
            start += limit

    def get_post(self, post_id: int) -> Post:
        data = self.request_json("GET", f"/posts/{post_id}")
        try:
            return Post.model_validate(data)
        except ValidationError as e:
            raise APIClientError("Ответ /posts/ имеет неожиданную структуру") from e

    def get_comments_for_post(self, post_id: int) -> list[Comment]:
        data = self.request_json("GET", f"/posts/{post_id}/comments")
        try:
            return CommentsAdapter.validate_python(data)
        except ValidationError as e:
            raise APIClientError("Ответ /posts//comments имеет неожиданную структуру") from e

    def __enter__(self) -> "APIClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
