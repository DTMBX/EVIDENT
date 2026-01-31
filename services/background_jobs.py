"""
Background Jobs Service - Async Task Processing
================================================

Provides:
- Redis-backed job queue
- Priority scheduling
- Retry with exponential backoff
- Job status tracking
- Batch processing
- Webhook notifications
- Dead letter queue
"""

import json
import logging
import os
import signal
import threading
import time
import traceback
import uuid
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status states."""

    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    DEAD = "dead"  # Max retries exceeded


class JobPriority(Enum):
    """Job priority levels."""

    LOW = 0
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


class Job:
    """Represents a background job."""

    def __init__(
        self,
        job_type: str,
        payload: Dict[str, Any],
        job_id: Optional[str] = None,
        priority: int = JobPriority.NORMAL.value,
        max_retries: int = 3,
        retry_delay: int = 60,
        timeout: int = 300,
        user_id: Optional[int] = None,
        callback_url: Optional[str] = None,
        meta: Optional[Dict] = None,
    ):
        self.id = job_id or str(uuid.uuid4())
        self.type = job_type
        self.payload = payload
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.user_id = user_id
        self.callback_url = callback_url
        self.meta = meta or {}

        self.status = JobStatus.PENDING.value
        self.attempts = 0
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow().isoformat()
        self.started_at = None
        self.completed_at = None
        self.progress = 0.0

    def to_dict(self) -> Dict:
        """Serialize job to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "payload": self.payload,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "user_id": self.user_id,
            "callback_url": self.callback_url,
            "meta": self.meta,
            "status": self.status,
            "attempts": self.attempts,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.progress,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Job":
        """Deserialize job from dictionary."""
        job = cls(
            job_type=data["type"],
            payload=data["payload"],
            job_id=data["id"],
            priority=data.get("priority", JobPriority.NORMAL.value),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 60),
            timeout=data.get("timeout", 300),
            user_id=data.get("user_id"),
            callback_url=data.get("callback_url"),
            meta=data.get("meta", {}),
        )
        job.status = data.get("status", JobStatus.PENDING.value)
        job.attempts = data.get("attempts", 0)
        job.result = data.get("result")
        job.error = data.get("error")
        job.created_at = data.get("created_at", job.created_at)
        job.started_at = data.get("started_at")
        job.completed_at = data.get("completed_at")
        job.progress = data.get("progress", 0.0)
        return job


class JobQueue:
    """
    Redis-backed job queue with priority scheduling.

    Features:
    - Priority-based processing
    - Retry with exponential backoff
    - Job status tracking
    - Timeout handling
    - Webhook notifications
    """

    QUEUE_KEY = "barberx:jobs:queue"
    PROCESSING_KEY = "barberx:jobs:processing"
    DEAD_LETTER_KEY = "barberx:jobs:dead"
    JOB_PREFIX = "barberx:jobs:job:"

    def __init__(self, redis_url: Optional[str] = None):
        self.redis = None
        self.connected = False
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._workers: List[threading.Thread] = []

        self._connect(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    def _connect(self, redis_url: str) -> bool:
        """Connect to Redis."""
        try:
            import redis

            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            self.connected = True
            logger.info("Job queue connected to Redis")
            return True
        except Exception as e:
            logger.warning(f"Job queue Redis connection failed: {e}")
            self._pending_jobs: List[Job] = []
            return False

    def register_handler(self, job_type: str, handler: Callable):
        """
        Register a handler for a job type.

        Args:
            job_type: Job type string
            handler: Callable(job: Job) -> Any
        """
        self._handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")

    def handler(self, job_type: str):
        """Decorator to register job handler."""

        def decorator(func: Callable):
            self.register_handler(job_type, func)
            return func

        return decorator

    def enqueue(self, job: Job) -> str:
        """
        Add job to queue.

        Returns:
            Job ID
        """
        job.status = JobStatus.QUEUED.value

        try:
            if self.connected and self.redis:
                # Store job data
                self.redis.setex(
                    f"{self.JOB_PREFIX}{job.id}",
                    86400 * 7,  # 7 day retention
                    json.dumps(job.to_dict()),
                )

                # Add to priority queue
                self.redis.zadd(self.QUEUE_KEY, {job.id: -job.priority})

                logger.debug(f"Enqueued job {job.id} ({job.type})")
            else:
                self._pending_jobs.append(job)

            return job.id

        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            raise

    def enqueue_many(self, jobs: List[Job]) -> List[str]:
        """Enqueue multiple jobs at once."""
        job_ids = []

        try:
            if self.connected and self.redis:
                pipe = self.redis.pipeline()

                for job in jobs:
                    job.status = JobStatus.QUEUED.value
                    pipe.setex(f"{self.JOB_PREFIX}{job.id}", 86400 * 7, json.dumps(job.to_dict()))
                    pipe.zadd(self.QUEUE_KEY, {job.id: -job.priority})
                    job_ids.append(job.id)

                pipe.execute()
            else:
                for job in jobs:
                    job_ids.append(self.enqueue(job))

            return job_ids

        except Exception as e:
            logger.error(f"Failed to enqueue batch: {e}")
            raise

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        try:
            if self.connected and self.redis:
                data = self.redis.get(f"{self.JOB_PREFIX}{job_id}")
                if data:
                    return Job.from_dict(json.loads(data))
            else:
                for job in self._pending_jobs:
                    if job.id == job_id:
                        return job
            return None

        except Exception as e:
            logger.error(f"Failed to get job: {e}")
            return None

    def update_job(self, job: Job) -> bool:
        """Update job data."""
        try:
            if self.connected and self.redis:
                self.redis.setex(f"{self.JOB_PREFIX}{job.id}", 86400 * 7, json.dumps(job.to_dict()))
            return True

        except Exception as e:
            logger.error(f"Failed to update job: {e}")
            return False

    def update_progress(self, job_id: str, progress: float, message: Optional[str] = None) -> bool:
        """Update job progress (0.0 to 1.0)."""
        job = self.get_job(job_id)
        if job:
            job.progress = min(1.0, max(0.0, progress))
            if message:
                job.meta["progress_message"] = message
            return self.update_job(job)
        return False

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending/queued job."""
        job = self.get_job(job_id)
        if job and job.status in [JobStatus.PENDING.value, JobStatus.QUEUED.value]:
            job.status = JobStatus.CANCELLED.value
            job.completed_at = datetime.utcnow().isoformat()
            self.update_job(job)

            if self.connected and self.redis:
                self.redis.zrem(self.QUEUE_KEY, job_id)

            return True
        return False

    def _dequeue(self) -> Optional[Job]:
        """Dequeue next job from queue."""
        try:
            if self.connected and self.redis:
                # Get highest priority job
                result = self.redis.zpopmin(self.QUEUE_KEY, count=1)
                if result:
                    job_id = result[0][0]
                    job = self.get_job(job_id)
                    if job:
                        # Track processing
                        self.redis.sadd(self.PROCESSING_KEY, job_id)
                        return job
            else:
                if self._pending_jobs:
                    self._pending_jobs.sort(key=lambda j: -j.priority)
                    return self._pending_jobs.pop(0)

            return None

        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None

    def _process_job(self, job: Job) -> bool:
        """Process a single job."""
        handler = self._handlers.get(job.type)

        if not handler:
            logger.error(f"No handler for job type: {job.type}")
            job.status = JobStatus.FAILED.value
            job.error = f"No handler registered for job type: {job.type}"
            self.update_job(job)
            return False

        job.status = JobStatus.PROCESSING.value
        job.attempts += 1
        job.started_at = datetime.utcnow().isoformat()
        self.update_job(job)

        try:
            # Execute with timeout
            result = handler(job)

            job.status = JobStatus.COMPLETED.value
            job.result = result
            job.completed_at = datetime.utcnow().isoformat()
            job.progress = 1.0
            self.update_job(job)

            # Send webhook if configured
            if job.callback_url:
                self._send_webhook(job)

            logger.info(f"Job {job.id} completed successfully")
            return True

        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()

            logger.error(f"Job {job.id} failed: {error_msg}\n{error_trace}")

            job.error = error_msg

            # Check if should retry
            if job.attempts < job.max_retries:
                job.status = JobStatus.RETRYING.value
                self.update_job(job)

                # Schedule retry with exponential backoff
                delay = job.retry_delay * (2 ** (job.attempts - 1))
                self._schedule_retry(job, delay)

                logger.info(f"Job {job.id} scheduled for retry in {delay}s")
            else:
                job.status = JobStatus.DEAD.value
                job.completed_at = datetime.utcnow().isoformat()
                self.update_job(job)

                # Move to dead letter queue
                if self.connected and self.redis:
                    self.redis.lpush(self.DEAD_LETTER_KEY, job.id)

                logger.error(f"Job {job.id} moved to dead letter queue")

            return False

        finally:
            # Remove from processing set
            if self.connected and self.redis:
                self.redis.srem(self.PROCESSING_KEY, job.id)

    def _schedule_retry(self, job: Job, delay: int):
        """Schedule job for retry after delay."""
        try:
            if self.connected and self.redis:
                # Use sorted set for delayed jobs
                retry_at = time.time() + delay
                self.redis.zadd(f"{self.QUEUE_KEY}:delayed", {job.id: retry_at})
            else:
                # Simple delay for memory mode
                time.sleep(delay)
                self.enqueue(job)

        except Exception as e:
            logger.error(f"Failed to schedule retry: {e}")

    def _process_delayed_jobs(self):
        """Move delayed jobs that are ready to main queue."""
        try:
            if self.connected and self.redis:
                now = time.time()
                # Get jobs that are ready
                ready = self.redis.zrangebyscore(
                    f"{self.QUEUE_KEY}:delayed", 0, now, start=0, num=10
                )

                for job_id in ready:
                    job = self.get_job(job_id)
                    if job:
                        job.status = JobStatus.QUEUED.value
                        self.update_job(job)
                        self.redis.zadd(self.QUEUE_KEY, {job_id: -job.priority})
                        self.redis.zrem(f"{self.QUEUE_KEY}:delayed", job_id)

        except Exception as e:
            logger.error(f"Failed to process delayed jobs: {e}")

    def _send_webhook(self, job: Job):
        """Send webhook notification for completed job."""
        if not job.callback_url:
            return

        try:
            import requests

            payload = {
                "job_id": job.id,
                "job_type": job.type,
                "status": job.status,
                "result": job.result,
                "error": job.error,
                "completed_at": job.completed_at,
            }

            response = requests.post(
                job.callback_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"},
            )

            logger.debug(f"Webhook sent to {job.callback_url}: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")

    # ==================== WORKER MANAGEMENT ====================

    def start_worker(self, num_workers: int = 1):
        """Start background worker threads."""
        self._running = True

        for i in range(num_workers):
            worker = threading.Thread(target=self._worker_loop, name=f"JobWorker-{i}", daemon=True)
            worker.start()
            self._workers.append(worker)

        # Start delayed job processor
        delayed_worker = threading.Thread(
            target=self._delayed_job_loop, name="DelayedJobWorker", daemon=True
        )
        delayed_worker.start()
        self._workers.append(delayed_worker)

        logger.info(f"Started {num_workers} job workers")

    def stop_worker(self, wait: bool = True, timeout: float = 30):
        """Stop all workers."""
        self._running = False

        if wait:
            for worker in self._workers:
                worker.join(timeout=timeout)

        self._workers.clear()
        logger.info("Job workers stopped")

    def _worker_loop(self):
        """Main worker loop."""
        while self._running:
            try:
                job = self._dequeue()

                if job:
                    self._process_job(job)
                else:
                    # No jobs, wait a bit
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(5)

    def _delayed_job_loop(self):
        """Process delayed jobs periodically."""
        while self._running:
            try:
                self._process_delayed_jobs()
                time.sleep(5)
            except Exception as e:
                logger.error(f"Delayed job processor error: {e}")
                time.sleep(10)

    # ==================== QUEUE STATS ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        stats = {
            "connected": self.connected,
            "handlers_registered": len(self._handlers),
            "workers_running": len([w for w in self._workers if w.is_alive()]),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.connected and self.redis:
            try:
                stats["queued"] = self.redis.zcard(self.QUEUE_KEY)
                stats["processing"] = self.redis.scard(self.PROCESSING_KEY)
                stats["delayed"] = self.redis.zcard(f"{self.QUEUE_KEY}:delayed")
                stats["dead"] = self.redis.llen(self.DEAD_LETTER_KEY)
            except Exception:
                pass
        else:
            stats["queued"] = len(self._pending_jobs)
            stats["processing"] = 0
            stats["delayed"] = 0
            stats["dead"] = 0

        return stats

    def get_dead_letter_jobs(self, limit: int = 100) -> List[Job]:
        """Get jobs from dead letter queue."""
        jobs = []

        try:
            if self.connected and self.redis:
                job_ids = self.redis.lrange(self.DEAD_LETTER_KEY, 0, limit - 1)
                for job_id in job_ids:
                    job = self.get_job(job_id)
                    if job:
                        jobs.append(job)
        except Exception as e:
            logger.error(f"Failed to get dead letter jobs: {e}")

        return jobs

    def retry_dead_letter_job(self, job_id: str) -> bool:
        """Retry a job from the dead letter queue."""
        job = self.get_job(job_id)

        if job and job.status == JobStatus.DEAD.value:
            job.status = JobStatus.QUEUED.value
            job.attempts = 0
            job.error = None
            self.update_job(job)

            if self.connected and self.redis:
                self.redis.lrem(self.DEAD_LETTER_KEY, 1, job_id)
                self.redis.zadd(self.QUEUE_KEY, {job_id: -job.priority})

            return True

        return False


# ============================================================
# PREDEFINED JOB HANDLERS
# ============================================================


def document_analysis_handler(job: Job) -> Dict:
    """Handler for document analysis jobs."""
    document_id = job.payload.get("document_id")
    analysis_types = job.payload.get("analysis_types", ["summary"])

    result = {"document_id": document_id, "analysis_types": analysis_types, "results": {}}

    # Import and use analysis service
    try:
        from services.chatbot_intelligence import LegalChatbotIntelligence

        chatbot = LegalChatbotIntelligence()

        for analysis_type in analysis_types:
            if analysis_type == "summary":
                result["results"]["summary"] = "Document summary placeholder"
            elif analysis_type == "entities":
                result["results"]["entities"] = {}
            elif analysis_type == "citations":
                result["results"]["citations"] = []
    except Exception as e:
        logger.error(f"Document analysis error: {e}")
        result["error"] = str(e)

    return result


def batch_document_analysis_handler(job: Job) -> Dict:
    """Handler for batch document analysis."""
    document_ids = job.payload.get("document_ids", [])
    analysis_types = job.payload.get("analysis_types", ["summary"])

    results = []
    total = len(document_ids)

    for i, doc_id in enumerate(document_ids):
        try:
            # Update progress
            job_queue.update_progress(
                job.id, (i + 1) / total, f"Processing document {i + 1} of {total}"
            )

            # Process document
            result = document_analysis_handler(
                Job(
                    job_type="document_analysis",
                    payload={"document_id": doc_id, "analysis_types": analysis_types},
                )
            )
            results.append(result)

        except Exception as e:
            results.append({"document_id": doc_id, "error": str(e)})

    return {
        "total_documents": total,
        "successful": len([r for r in results if "error" not in r]),
        "failed": len([r for r in results if "error" in r]),
        "results": results,
    }


def citation_validation_handler(job: Job) -> Dict:
    """Handler for citation validation jobs."""
    citations = job.payload.get("citations", [])

    results = []
    for citation in citations:
        results.append(
            {"citation": citation, "valid": True, "normalized": citation.strip()}  # Placeholder
        )

    return {"results": results}


# ============================================================
# GLOBAL INSTANCE
# ============================================================

job_queue = JobQueue()

# Register default handlers
job_queue.register_handler("document_analysis", document_analysis_handler)
job_queue.register_handler("batch_document_analysis", batch_document_analysis_handler)
job_queue.register_handler("citation_validation", citation_validation_handler)


def get_job_queue() -> JobQueue:
    """Get the global job queue instance."""
    return job_queue


def start_workers(num_workers: int = 2):
    """Start job workers."""
    job_queue.start_worker(num_workers)


def stop_workers():
    """Stop job workers."""
    job_queue.stop_worker()
