"""
services/prefetch_service.py — background pre-resolution of upcoming stream URLs.

How it works
────────────
1. Whenever a track list is known (album loaded, search results returned, top
   songs fetched) the caller registers the ordered list of video IDs:

       prefetch_service.register_queue(["id1", "id2", "id3", ...])

   The service records "id2 follows id1", "id3 follows id2", etc.

2. The moment a track *starts playing* (i.e. /stream is called) the caller
   notifies us:

       prefetch_service.on_stream_started("id1", cache_ttl=3600)

   We look up the next `prefetch_ahead` IDs and submit each one to a small
   background thread pool that calls resolve_url() — which writes into the
   shared _StreamCache.

3. By the time the user skips to the next track, its CDN URL is already in
   cache → minimal latency.

Configuration (via app.config["STREAM"])
─────────────────────────────────────────
  prefetch_ahead   int  (default 2) — how many upcoming tracks to warm
  prefetch_workers int  (default 3) — thread-pool size
  cache_ttl        int  (default 3600) — forwarded to resolve_url

The service is intentionally forgiving: every operation is best-effort and
logged at DEBUG/INFO level; it never raises.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

log = logging.getLogger(__name__)

# Imported lazily inside methods to avoid circular imports at module load time.
# resolve_url lives in stream_service and uses the shared _StreamCache.


class PrefetchService:
    def __init__(self):
        # video_id → ordered list of video IDs that follow it
        self._registry: dict[str, list[str]] = {}
        # video IDs currently being resolved in the background
        self._in_flight: set[str] = set()
        self._lock      = threading.Lock()
        # Pool is created lazily so config values can be injected later
        self._pool: Optional[ThreadPoolExecutor] = None
        self._pool_size: int = 3

    # ── public API ────────────────────────────────────────────────────────────

    def configure(self, workers: int = 3):
        """
        Initialise (or re-initialise) the thread pool.
        Safe to call repeatedly — only recreates the pool when the worker
        count changes, so calling it on every stream request is cheap.
        """
        workers = max(1, workers)
        if self._pool is not None and workers == self._pool_size:
            return  # nothing to do
        if self._pool is not None:
            self._pool.shutdown(wait=False)
        self._pool_size = workers
        self._pool = ThreadPoolExecutor(
            max_workers=self._pool_size,
            thread_name_prefix="prefetch",
        )
        log.info("PrefetchService configured: workers=%d", self._pool_size)

    def register_queue(self, video_ids: list[str]):
        """
        Register an ordered sequence of video IDs (e.g. an album's track list).

        For each position i we record video_ids[i+1:] as the 'coming next' list
        so that on_stream_started(video_ids[i]) knows what to prefetch.
        """
        ids = [v for v in video_ids if v]   # strip empties
        if len(ids) < 2:
            return

        with self._lock:
            for i, vid in enumerate(ids):
                tail = ids[i + 1:]
                # Merge with any existing tail to handle overlapping contexts
                existing = self._registry.get(vid, [])
                merged   = _merge_lists(existing, tail)
                self._registry[vid] = merged

        log.debug("register_queue: %d IDs, first=%s", len(ids), ids[0])

    def on_stream_started(self, video_id: str, cache_ttl: int = 3600,
                          prefetch_ahead: int = 2):
        """
        Called when playback of *video_id* begins.  Schedules background
        resolution for the next *prefetch_ahead* tracks in the known queue.
        """
        self._ensure_pool()

        with self._lock:
            upcoming = list(self._registry.get(video_id, []))

        targets = upcoming[:prefetch_ahead]
        if not targets:
            log.debug("on_stream_started(%s): no upcoming tracks known", video_id)
            return

        log.info("on_stream_started(%s): scheduling prefetch for %s",
                 video_id, targets)

        for target_id in targets:
            self._submit(target_id, cache_ttl)

    def prefetch_explicit(self, video_ids: list[str], cache_ttl: int = 3600):
        """
        Directly schedule prefetch for an explicit list of IDs.
        Useful for warming the very first track before it is played.
        """
        self._ensure_pool()
        for vid in video_ids:
            if vid:
                self._submit(vid, cache_ttl)

    def status(self) -> dict:
        """Return a snapshot of internal state (for diagnostics)."""
        with self._lock:
            return {
                "registry_size": len(self._registry),
                "in_flight":     list(self._in_flight),
                "pool_size":     self._pool_size,
            }

    # ── internals ─────────────────────────────────────────────────────────────

    def _ensure_pool(self):
        if self._pool is None:
            self._pool = ThreadPoolExecutor(
                max_workers=self._pool_size,
                thread_name_prefix="prefetch",
            )

    def _submit(self, video_id: str, cache_ttl: int):
        with self._lock:
            if video_id in self._in_flight:
                log.debug("prefetch %s: already in flight, skipping", video_id)
                return
            self._in_flight.add(video_id)

        future: Future = self._pool.submit(
            self._resolve_worker, video_id, cache_ttl
        )
        future.add_done_callback(lambda f: self._on_done(video_id, f))

    def _resolve_worker(self, video_id: str, cache_ttl: int) -> bool:
        """Runs in the thread pool.  Returns True if URL was resolved."""
        # Import here to avoid circular dependency at module load time
        from services.stream_service import resolve_url, _cache

        # If it's already in cache, nothing to do
        if _cache.get(video_id, cache_ttl):
            log.debug("prefetch %s: already cached", video_id)
            return True

        log.info("prefetch %s: resolving…", video_id)
        url = resolve_url(video_id, cache_ttl)
        if url:
            log.info("prefetch %s: OK", video_id)
            return True
        else:
            log.warning("prefetch %s: failed to resolve", video_id)
            return False

    def _on_done(self, video_id: str, future: Future):
        with self._lock:
            self._in_flight.discard(video_id)
        if future.exception():
            log.error("prefetch %s raised: %s", video_id, future.exception())


# ── helpers ───────────────────────────────────────────────────────────────────

def _merge_lists(existing: list[str], incoming: list[str]) -> list[str]:
    """
    Combine two ordered lists, preserving incoming order and de-duplicating.
    incoming takes precedence if they share IDs.
    """
    seen   = set(incoming)
    extras = [x for x in existing if x not in seen]
    return incoming + extras


# Singleton
prefetch_service = PrefetchService()
