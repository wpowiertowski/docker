import asyncio
import hashlib
import hmac
import json
import logging
import sys

from aiohttp import web

from .config import Config
from .queue_manager import QueueManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


def _verify_signature(secret: str, body: bytes, sig_header: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_header)


async def handle_webhook(request: web.Request) -> web.Response:
    body = await request.read()
    sig = request.headers.get("X-Hub-Signature-256", "")
    cfg: Config = request.app["cfg"]

    if not _verify_signature(cfg.github_webhook_secret, body, sig):
        log.warning("Rejected webhook — invalid signature from %s", request.remote)
        raise web.HTTPForbidden(reason="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event != "workflow_job":
        return web.Response(text="ignored")

    payload = json.loads(body)
    action = payload.get("action")
    queue: QueueManager = request.app["queue"]

    if action == "queued":
        asyncio.create_task(queue.enqueue(payload))
    elif action == "completed":
        asyncio.create_task(queue.job_completed(payload))

    return web.Response(text="ok")


async def handle_health(_request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def handle_status(request: web.Request) -> web.Response:
    queue: QueueManager = request.app["queue"]
    return web.json_response({
        "worker_state": queue.state.name,
        "queue_depth": queue.queue_size,
    })


async def on_startup(app: web.Application) -> None:
    app["queue"].start()
    log.info("Coordinator ready on :8080")


def main() -> None:
    cfg = Config.from_env()
    queue = QueueManager(cfg)

    app = web.Application()
    app["cfg"] = cfg
    app["queue"] = queue
    app.on_startup.append(on_startup)

    app.router.add_post("/webhook", handle_webhook)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/status", handle_status)

    web.run_app(app, host="0.0.0.0", port=8080, access_log=None)


if __name__ == "__main__":
    main()
