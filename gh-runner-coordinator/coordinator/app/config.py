import os
from dataclasses import dataclass


def _require(key: str) -> str:
    val = os.environ.get(key, "").strip()
    if not val:
        raise RuntimeError(f"Required environment variable {key!r} is not set")
    return val


def _optional(key: str, default: str) -> str:
    return os.environ.get(key, default).strip() or default


@dataclass(frozen=True)
class Config:
    github_webhook_secret: str
    github_token: str
    github_repo: str
    runner_labels: str

    worker_mac: str
    worker_host: str
    worker_ssh_user: str
    worker_ssh_key: str
    worker_runner_dir: str
    worker_suspend_cmd: str

    worker_online_timeout: int
    worker_online_poll_interval: int
    suspend_grace_seconds: int

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            github_webhook_secret=_require("GITHUB_WEBHOOK_SECRET"),
            github_token=_require("GITHUB_TOKEN"),
            github_repo=_require("GITHUB_REPO"),
            runner_labels=_optional("RUNNER_LABELS", "self-hosted,physical-worker"),
            worker_mac=_require("WORKER_MAC"),
            worker_host=_require("WORKER_HOST"),
            worker_ssh_user=_optional("WORKER_SSH_USER", "runner"),
            worker_ssh_key=_optional("WORKER_SSH_KEY", "/ssh/id_rsa"),
            worker_runner_dir=_optional("WORKER_RUNNER_DIR", "/home/runner/actions-runner"),
            worker_suspend_cmd=_optional("WORKER_SUSPEND_CMD", "systemctl suspend"),
            worker_online_timeout=int(_optional("WORKER_ONLINE_TIMEOUT", "120")),
            worker_online_poll_interval=int(_optional("WORKER_ONLINE_POLL_INTERVAL", "5")),
            suspend_grace_seconds=int(_optional("SUSPEND_GRACE_SECONDS", "30")),
        )
