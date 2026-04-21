from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import httpx
from loguru import logger

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GraphACLError(Exception):
    """Base class for MS Graph ACL errors."""


class GraphAuthenticationError(GraphACLError):
    """HTTP 401 — token missing, invalid, or expired. Fails the whole batch."""


class GraphRateLimitError(GraphACLError):
    """HTTP 429 — MS Graph rate limit hit. Caller should back off."""


class GraphAPIError(GraphACLError):
    """HTTP 5xx or unexpected status — logged and treated as check_failed."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(f"Graph API error {status_code}: {detail}")
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VideoIdentifier:
    video_id: str
    drive_id: str
    item_id: str


@dataclass
class AccessCheckResult:
    access_allowed: list[str] = field(default_factory=list)
    access_denied: list[str] = field(default_factory=list)
    check_failed: list[str] = field(default_factory=list)


# Internal result container that retains video_id across gather() boundaries.
@dataclass
class _SingleResult:
    video_id: str
    granted: bool | None  # None means an error occurred
    error: Exception | None = None


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


async def check_access_to_video(
    client: httpx.AsyncClient,
    graph_token: str,
    drive_id: str,
    item_id: str,
) -> bool:
    """Return True if the token bearer has read access to the given OneDrive item."""
    url = f"{GRAPH_API_BASE}/drives/{drive_id}/items/{item_id}"
    headers = {"Authorization": f"Bearer {graph_token}"}

    logger.debug("Checking Graph access drive_id={} item_id={}", drive_id, item_id)

    response = await client.get(url, headers=headers)
    status = response.status_code

    if status == 200:
        body = response.json()
        if body.get("id") != item_id:
            raise GraphAPIError(200, f"item_id mismatch: expected {item_id}, got {body.get('id')}")
        logger.debug("Access granted drive_id={} item_id={}", drive_id, item_id)
        return True

    if status in (403, 404):
        logger.debug("Access denied ({}) drive_id={} item_id={}", status, drive_id, item_id)
        return False

    if status == 401:
        logger.warning("Graph authentication failure drive_id={} item_id={}", drive_id, item_id)
        raise GraphAuthenticationError("MS Graph returned 401 — token invalid or expired")

    if status == 429:
        logger.warning("Graph rate limit hit drive_id={} item_id={}", drive_id, item_id)
        raise GraphRateLimitError("MS Graph returned 429 — rate limited")

    logger.warning(
        "Unexpected Graph status {} drive_id={} item_id={}", status, drive_id, item_id
    )
    raise GraphAPIError(status, response.text[:200])


async def check_access_to_video_list(
    graph_token: str,
    video_identifiers: list[VideoIdentifier],
    *,
    max_concurrency: int = 10,
) -> AccessCheckResult:
    """Check MS Graph access for a batch of videos, returning a three-bucket result."""
    if not video_identifiers:
        return AccessCheckResult()

    semaphore = asyncio.Semaphore(max_concurrency)

    async def _check_one(client: httpx.AsyncClient, vid: VideoIdentifier) -> _SingleResult:
        async with semaphore:
            try:
                granted = await check_access_to_video(
                    client, graph_token, vid.drive_id, vid.item_id
                )
                return _SingleResult(video_id=vid.video_id, granted=granted)
            except (GraphAuthenticationError, GraphRateLimitError):
                raise  # propagate — fail the whole batch
            except Exception as exc:
                logger.warning(
                    "Graph API error for drive_id={} item_id={}: {}",
                    vid.drive_id,
                    vid.item_id,
                    exc,
                )
                return _SingleResult(video_id=vid.video_id, granted=None, error=exc)

    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [_check_one(client, vid) for vid in video_identifiers]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    result = AccessCheckResult()
    for raw in raw_results:
        # GraphAuthenticationError / GraphRateLimitError bubble up through gather as exceptions
        if isinstance(raw, (GraphAuthenticationError, GraphRateLimitError)):
            raise raw
        if isinstance(raw, Exception):
            raise raw  # unexpected — propagate
        assert isinstance(raw, _SingleResult)
        if raw.granted is True:
            result.access_allowed.append(raw.video_id)
        elif raw.granted is False:
            result.access_denied.append(raw.video_id)
        else:
            result.check_failed.append(raw.video_id)

    return result
