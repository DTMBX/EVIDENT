"""
Redis Cache Service - High-Performance Caching Layer
=====================================================

Provides:
- Response caching with TTL
- Embedding caching for AI/ML
- Session management
- Rate limiting
- Distributed locking
- Pub/Sub for real-time updates
"""

import hashlib
import json
import logging
import os
import pickle
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Production-grade Redis caching with fallback to in-memory.

    Features:
    - Automatic connection pooling
    - Circuit breaker for failures
    - Compression for large values
    - Key prefixing and namespacing
    - TTL management
    - Metrics collection
    """

    DEFAULT_TTL = 3600  # 1 hour
    MAX_VALUE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(
        self,
        redis_url: Optional[str] = None,
        prefix: str = "barberx",
        default_ttl: int = DEFAULT_TTL,
        enable_compression: bool = True,
    ):
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.enable_compression = enable_compression
        self.redis = None
        self.connected = False
        self._memory_cache: Dict[str, Any] = {}
        self._memory_ttl: Dict[str, float] = {}
        self._stats = {"hits": 0, "misses": 0, "errors": 0, "sets": 0}

        self._connect(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    def _connect(self, redis_url: str) -> bool:
        """Establish Redis connection with pooling."""
        try:
            import redis
            from redis.connection import ConnectionPool

            pool = ConnectionPool.from_url(
                redis_url,
                max_connections=20,
                decode_responses=False,  # Handle binary for compression
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )

            self.redis = redis.Redis(connection_pool=pool)
            self.redis.ping()
            self.connected = True
            logger.info(
                f"Redis connected: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}"
            )
            return True

        except ImportError:
            logger.warning("redis package not installed, using memory cache")
            return False
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using memory cache")
            return False

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"{self.prefix}:{key}"

    def _hash_key(self, data: Any) -> str:
        """Create hash from complex data for cache key."""
        if isinstance(data, str):
            return hashlib.sha256(data.encode()).hexdigest()[:16]
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        data = pickle.dumps(value)

        if self.enable_compression and len(data) > 1024:
            import zlib

            compressed = zlib.compress(data, level=6)
            if len(compressed) < len(data):
                return b"Z:" + compressed

        return b"P:" + data

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize stored value."""
        if data is None:
            return None

        if data.startswith(b"Z:"):
            import zlib

            data = zlib.decompress(data[2:])
        elif data.startswith(b"P:"):
            data = data[2:]

        return pickle.loads(data)

    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache."""
        now = time.time()
        expired = [k for k, ttl in self._memory_ttl.items() if ttl < now]
        for key in expired:
            self._memory_cache.pop(key, None)
            self._memory_ttl.pop(key, None)

    # ==================== CORE OPERATIONS ====================

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get cached value.

        Args:
            key: Cache key
            default: Default if not found

        Returns:
            Cached value or default
        """
        full_key = self._make_key(key)

        try:
            if self.connected and self.redis:
                data = self.redis.get(full_key)
                if data is not None:
                    self._stats["hits"] += 1
                    return self._deserialize(data)
            else:
                self._cleanup_memory_cache()
                if full_key in self._memory_cache:
                    if self._memory_ttl.get(full_key, 0) > time.time():
                        self._stats["hits"] += 1
                        return self._memory_cache[full_key]
                    else:
                        del self._memory_cache[full_key]
                        del self._memory_ttl[full_key]

            self._stats["misses"] += 1
            return default

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache get error: {e}")
            return default

    def set(
        self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False, xx: bool = False
    ) -> bool:
        """
        Set cached value.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            nx: Only set if not exists
            xx: Only set if exists

        Returns:
            True if set successfully
        """
        full_key = self._make_key(key)
        ttl = ttl or self.default_ttl

        try:
            serialized = self._serialize(value)

            if len(serialized) > self.MAX_VALUE_SIZE:
                logger.warning(f"Value too large for cache: {len(serialized)} bytes")
                return False

            if self.connected and self.redis:
                result = self.redis.set(full_key, serialized, ex=ttl, nx=nx, xx=xx)
                if result:
                    self._stats["sets"] += 1
                return bool(result)
            else:
                if nx and full_key in self._memory_cache:
                    return False
                if xx and full_key not in self._memory_cache:
                    return False

                self._memory_cache[full_key] = value
                self._memory_ttl[full_key] = time.time() + ttl
                self._stats["sets"] += 1
                return True

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete cached value."""
        full_key = self._make_key(key)

        try:
            if self.connected and self.redis:
                return bool(self.redis.delete(full_key))
            else:
                self._memory_cache.pop(full_key, None)
                self._memory_ttl.pop(full_key, None)
                return True

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        full_key = self._make_key(key)

        try:
            if self.connected and self.redis:
                return bool(self.redis.exists(full_key))
            else:
                self._cleanup_memory_cache()
                return full_key in self._memory_cache

        except Exception:
            return False

    def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        full_key = self._make_key(key)

        try:
            if self.connected and self.redis:
                return self.redis.ttl(full_key)
            else:
                expire_time = self._memory_ttl.get(full_key, 0)
                return max(0, int(expire_time - time.time()))

        except Exception:
            return -1

    def expire(self, key: str, ttl: int) -> bool:
        """Set new TTL for existing key."""
        full_key = self._make_key(key)

        try:
            if self.connected and self.redis:
                return bool(self.redis.expire(full_key, ttl))
            else:
                if full_key in self._memory_cache:
                    self._memory_ttl[full_key] = time.time() + ttl
                    return True
                return False

        except Exception:
            return False

    # ==================== BATCH OPERATIONS ====================

    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values at once."""
        full_keys = [self._make_key(k) for k in keys]
        result = {}

        try:
            if self.connected and self.redis:
                values = self.redis.mget(full_keys)
                for key, value in zip(keys, values):
                    if value is not None:
                        result[key] = self._deserialize(value)
                        self._stats["hits"] += 1
                    else:
                        self._stats["misses"] += 1
            else:
                self._cleanup_memory_cache()
                for key, full_key in zip(keys, full_keys):
                    if full_key in self._memory_cache:
                        result[key] = self._memory_cache[full_key]
                        self._stats["hits"] += 1
                    else:
                        self._stats["misses"] += 1

            return result

        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return {}

    def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values at once."""
        ttl = ttl or self.default_ttl

        try:
            if self.connected and self.redis:
                pipe = self.redis.pipeline()
                for key, value in mapping.items():
                    full_key = self._make_key(key)
                    serialized = self._serialize(value)
                    pipe.setex(full_key, ttl, serialized)
                pipe.execute()
            else:
                for key, value in mapping.items():
                    full_key = self._make_key(key)
                    self._memory_cache[full_key] = value
                    self._memory_ttl[full_key] = time.time() + ttl

            self._stats["sets"] += len(mapping)
            return True

        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        full_pattern = self._make_key(pattern)
        count = 0

        try:
            if self.connected and self.redis:
                cursor = 0
                while True:
                    cursor, keys = self.redis.scan(cursor, match=full_pattern, count=100)
                    if keys:
                        count += self.redis.delete(*keys)
                    if cursor == 0:
                        break
            else:
                to_delete = [
                    k
                    for k in self._memory_cache.keys()
                    if k.startswith(full_pattern.replace("*", ""))
                ]
                for key in to_delete:
                    self._memory_cache.pop(key, None)
                    self._memory_ttl.pop(key, None)
                    count += 1

            return count

        except Exception as e:
            logger.error(f"Cache delete_pattern error: {e}")
            return 0

    # ==================== ATOMIC OPERATIONS ====================

    def incr(self, key: str, amount: int = 1) -> int:
        """Atomically increment value."""
        full_key = self._make_key(key)

        try:
            if self.connected and self.redis:
                return self.redis.incrby(full_key, amount)
            else:
                current = self._memory_cache.get(full_key, 0)
                new_value = current + amount
                self._memory_cache[full_key] = new_value
                return new_value

        except Exception:
            return 0

    def decr(self, key: str, amount: int = 1) -> int:
        """Atomically decrement value."""
        return self.incr(key, -amount)

    @contextmanager
    def lock(self, name: str, timeout: int = 10, blocking: bool = True):
        """
        Distributed lock using Redis.

        Usage:
            with cache.lock("my_lock"):
                # Critical section
        """
        lock_key = self._make_key(f"lock:{name}")
        lock_id = os.urandom(16).hex()
        acquired = False

        try:
            if self.connected and self.redis:
                acquired = self.redis.set(lock_key, lock_id, nx=True, ex=timeout)

                if not acquired and blocking:
                    start = time.time()
                    while time.time() - start < timeout:
                        time.sleep(0.1)
                        acquired = self.redis.set(lock_key, lock_id, nx=True, ex=timeout)
                        if acquired:
                            break
            else:
                acquired = True  # No locking in memory mode

            if not acquired:
                raise TimeoutError(f"Could not acquire lock: {name}")

            yield acquired

        finally:
            if acquired and self.connected and self.redis:
                # Only release if we own the lock
                if self.redis.get(lock_key) == lock_id.encode():
                    self.redis.delete(lock_key)

    # ==================== RATE LIMITING ====================

    def rate_limit(self, key: str, limit: int, window: int = 60) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.

        Args:
            key: Rate limit key (e.g., "user:123:api")
            limit: Max requests in window
            window: Window size in seconds

        Returns:
            (allowed: bool, remaining: int)
        """
        full_key = self._make_key(f"ratelimit:{key}")
        now = time.time()

        try:
            if self.connected and self.redis:
                pipe = self.redis.pipeline()
                pipe.zremrangebyscore(full_key, 0, now - window)
                pipe.zadd(full_key, {str(now): now})
                pipe.zcard(full_key)
                pipe.expire(full_key, window)
                _, _, count, _ = pipe.execute()

                remaining = max(0, limit - count)
                return count <= limit, remaining
            else:
                # Simple memory-based rate limiting
                requests = self._memory_cache.get(full_key, [])
                requests = [t for t in requests if t > now - window]
                requests.append(now)
                self._memory_cache[full_key] = requests

                remaining = max(0, limit - len(requests))
                return len(requests) <= limit, remaining

        except Exception as e:
            logger.error(f"Rate limit error: {e}")
            return True, limit  # Fail open

    # ==================== CACHING DECORATORS ====================

    def cached(
        self,
        ttl: Optional[int] = None,
        key_prefix: str = "",
        key_builder: Optional[Callable] = None,
    ):
        """
        Decorator to cache function results.

        Args:
            ttl: Cache TTL
            key_prefix: Prefix for cache key
            key_builder: Custom function to build cache key

        Usage:
            @cache.cached(ttl=300, key_prefix="user")
            def get_user(user_id):
                ...
        """

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    key_parts = [key_prefix or func.__name__]
                    key_parts.extend(str(a) for a in args)
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = ":".join(key_parts)

                # Check cache
                cached = self.get(cache_key)
                if cached is not None:
                    return cached

                # Execute function
                result = func(*args, **kwargs)

                # Cache result
                self.set(cache_key, result, ttl=ttl)

                return result

            # Add cache control methods
            wrapper.cache_key = lambda *args, **kwargs: (
                key_builder(*args, **kwargs) if key_builder else None
            )
            wrapper.invalidate = lambda *args, **kwargs: self.delete(
                wrapper.cache_key(*args, **kwargs)
            )

            return wrapper

        return decorator

    # ==================== STATS & MONITORING ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self._stats.copy()

        total = stats["hits"] + stats["misses"]
        stats["hit_rate"] = stats["hits"] / total if total > 0 else 0
        stats["connected"] = self.connected
        stats["backend"] = "redis" if self.connected else "memory"

        if self.connected and self.redis:
            try:
                info = self.redis.info("memory")
                stats["memory_used"] = info.get("used_memory_human", "N/A")
            except Exception:
                pass
        else:
            stats["memory_keys"] = len(self._memory_cache)

        return stats

    def health_check(self) -> Dict[str, Any]:
        """Health check for monitoring."""
        status = {
            "healthy": True,
            "connected": self.connected,
            "backend": "redis" if self.connected else "memory",
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.connected and self.redis:
            try:
                latency_start = time.time()
                self.redis.ping()
                status["latency_ms"] = round((time.time() - latency_start) * 1000, 2)
            except Exception as e:
                status["healthy"] = False
                status["error"] = str(e)

        return status

    def flush(self, confirm: bool = False) -> bool:
        """Flush all cached data (DANGEROUS)."""
        if not confirm:
            logger.warning("Flush called without confirmation")
            return False

        try:
            if self.connected and self.redis:
                # Only flush our namespace
                return self.delete_pattern("*") > 0
            else:
                self._memory_cache.clear()
                self._memory_ttl.clear()
                return True

        except Exception as e:
            logger.error(f"Flush error: {e}")
            return False


# ============================================================
# SPECIALIZED CACHES
# ============================================================


class EmbeddingCache(RedisCache):
    """Specialized cache for AI embeddings."""

    def __init__(self, redis_url: Optional[str] = None):
        super().__init__(
            redis_url=redis_url,
            prefix="barberx:embedding",
            default_ttl=86400 * 7,  # 7 days
            enable_compression=True,
        )

    def get_embedding(self, text: str, model: str = "default") -> Optional[List[float]]:
        """Get cached embedding for text."""
        key = f"{model}:{self._hash_key(text)}"
        return self.get(key)

    def set_embedding(
        self, text: str, embedding: List[float], model: str = "default", ttl: int = 86400 * 7
    ) -> bool:
        """Cache embedding."""
        key = f"{model}:{self._hash_key(text)}"
        return self.set(key, embedding, ttl=ttl)

    def get_batch_embeddings(
        self, texts: List[str], model: str = "default"
    ) -> Dict[str, Optional[List[float]]]:
        """Get cached embeddings for multiple texts."""
        keys = [f"{model}:{self._hash_key(t)}" for t in texts]
        results = self.mget(keys)
        return {text: results.get(key) for text, key in zip(texts, keys)}


class SessionCache(RedisCache):
    """Specialized cache for user sessions."""

    def __init__(self, redis_url: Optional[str] = None):
        super().__init__(
            redis_url=redis_url,
            prefix="barberx:session",
            default_ttl=3600 * 24,  # 24 hours
            enable_compression=False,
        )

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        return self.get(session_id)

    def set_session(self, session_id: str, data: Dict, ttl: int = 86400) -> bool:
        """Set session data."""
        return self.set(session_id, data, ttl=ttl)

    def extend_session(self, session_id: str, ttl: int = 86400) -> bool:
        """Extend session TTL."""
        return self.expire(session_id, ttl)

    def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        return self.delete(session_id)

    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        return self.delete_pattern(f"*:user:{user_id}:*")


# ============================================================
# GLOBAL INSTANCES
# ============================================================

# Main cache
cache = RedisCache()

# Specialized caches
embedding_cache = EmbeddingCache()
session_cache = SessionCache()


# Convenience function
def get_cache() -> RedisCache:
    """Get the global cache instance."""
    return cache
