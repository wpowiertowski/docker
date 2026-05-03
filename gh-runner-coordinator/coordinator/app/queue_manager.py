import asyncio
import logging
import time
from enum import Enum, auto

from .config import Config
from .github_client import get_registration_token
from . import worker_manager as wm

log = logging.getLogger(__name__)


class WorkerState(Enum):
    OFFLINE = auto()
    WAKING = auto()
    ONLINE = auto()
    RUNNING = auto()
    SUSPENDING = auto()


class QueueManager:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._queue: asyncio.Queue[dict] = asyncio.Queue()
        self._state = WorkerState.OFFLINE
        self._suspend_task: asyncio.Task | None = None
        self._job_counter = 0

    @property
    def state(self) -> WorkerState:
        return self._state

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    def start(self) -> None:
        asyncio.create_task(self._process_loop(), name="queue-processor")
        log.info("Queue processor started")

    async def enqueue(self, payload: dict) -> None:
        job_id = payload["workflow_job"]["id"]
        if self._suspend_task and not self._suspend_task.done():
            log.info("Job %s arrived — cancelling pending suspend", job_id)
            self._suspend_task.cancel()
        depth = self._queue.qsize() + 1
        log.info("Enqueued job %s (queue depth: %d)", job_id, depth)
        await self._queue.put(payload)

    async def job_completed(self, payload: dict) -> None:
        job_id = payload["workflow_job"]["id"]
        conclusion = payload["workflow_job"].get("conclusion", "unknown")
        log.info("GitHub reports job %s completed: %s", job_id, conclusion)

    async def _process_loop(self) -> None:
        while True:
            payload = await self._queue.get()
            try:
                await self._dispatch(payload)
            except Exception:
                log.exception("Unhandled error dispatching job — dropping")
            finally:
                self._queue.task_done()
                if self._queue.empty():
                    self._suspend_task = asyncio.create_task(
                        self._deferred_suspend(), name="deferred-suspend"
                    )

    async def _ensure_online(self) -> bool:
        if self._state != WorkerState.OFFLINE:
            # Confirm the worker is still reachable before trusting cached state
            if await wm.is_online(self.cfg):
                return True
            log.warning("Worker unreachable despite state=%s — attempting WoL", self._state.name)
            self._state = WorkerState.OFFLINE

        self._state = WorkerState.WAKING
        wm.wake(self.cfg)
        online = await wm.wait_online(self.cfg)
        if online:
            self._state = WorkerState.ONLINE
        else:
            self._state = WorkerState.OFFLINE
        return online

    async def _dispatch(self, payload: dict) -> None:
        job_id = payload["workflow_job"]["id"]
        log.info("Dispatching job %s (worker state: %s)", job_id, self._state.name)

        if not await self._ensure_online():
            log.error("Worker failed to come online — requeueing job %s", job_id)
            await self._queue.put(payload)
            return

        self._job_counter += 1
        runner_name = f"worker-{self._job_counter}-{int(time.time())}"
        self._state = WorkerState.RUNNING
        try:
            token = await get_registration_token(self.cfg)
            await wm.run_runner(self.cfg, token, runner_name)
        finally:
            self._state = WorkerState.ONLINE

    async def _deferred_suspend(self) -> None:
        grace = self.cfg.suspend_grace_seconds
        log.info("Queue empty — suspending worker in %ds if no jobs arrive", grace)
        try:
            await asyncio.sleep(grace)
            if self._queue.empty():
                self._state = WorkerState.SUSPENDING
                await wm.suspend(self.cfg)
                self._state = WorkerState.OFFLINE
                log.info("Worker suspended")
        except asyncio.CancelledError:
            log.info("Suspend cancelled — new job arrived in grace window")
