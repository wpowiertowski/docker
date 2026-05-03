import asyncio
import logging
import shlex
import socket

from .config import Config

log = logging.getLogger(__name__)


def _magic_packet(mac: str) -> bytes:
    mac_bytes = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    if len(mac_bytes) != 6:
        raise ValueError(f"Invalid MAC address: {mac!r}")
    return b"\xff" * 6 + mac_bytes * 16


def wake(cfg: Config) -> None:
    packet = _magic_packet(cfg.worker_mac)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(packet, ("255.255.255.255", 9))
    log.info("WoL magic packet sent to %s", cfg.worker_mac)


async def _tcp_probe(host: str, port: int = 22, timeout: float = 3.0) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError):
        return False


async def is_online(cfg: Config) -> bool:
    return await _tcp_probe(cfg.worker_host)


async def wait_online(cfg: Config) -> bool:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + cfg.worker_online_timeout
    while loop.time() < deadline:
        if await _tcp_probe(cfg.worker_host):
            log.info("Worker %s is online", cfg.worker_host)
            return True
        await asyncio.sleep(cfg.worker_online_poll_interval)
    log.error("Worker did not come online within %ds", cfg.worker_online_timeout)
    return False


def _ssh_cmd(cfg: Config) -> list[str]:
    return [
        "ssh",
        "-i", cfg.worker_ssh_key,
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=10",
        f"{cfg.worker_ssh_user}@{cfg.worker_host}",
    ]


async def run_runner(cfg: Config, token: str, runner_name: str) -> int:
    runner_dir = cfg.worker_runner_dir
    # Single-quoted token prevents shell expansion of special chars in the token value
    script = (
        f"cd {shlex.quote(runner_dir)} && "
        f"./config.sh"
        f" --url {shlex.quote(f'https://github.com/{cfg.github_repo}')}"
        f" --token {shlex.quote(token)}"
        f" --name {shlex.quote(runner_name)}"
        f" --labels {shlex.quote(cfg.runner_labels)}"
        f" --ephemeral"
        f" --unattended"
        f" --replace"
        f" && ./run.sh"
    )
    cmd = _ssh_cmd(cfg) + [script]
    log.info("Starting ephemeral runner %r on %s", runner_name, cfg.worker_host)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for line in proc.stdout:
        log.info("[runner] %s", line.decode().rstrip())
    rc = await proc.wait()
    log.info("Runner %r exited with code %d", runner_name, rc)
    return rc


async def suspend(cfg: Config) -> None:
    cmd = _ssh_cmd(cfg) + [cfg.worker_suspend_cmd]
    log.info("Suspending worker: %s", cfg.worker_suspend_cmd)
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.wait()
