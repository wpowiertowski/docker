#!/usr/bin/env python3
"""Track CPU, memory, network and disk usage of running containers and flag deviations.

Samples `docker stats` into SQLite, compares the latest samples against a
7-day per-container baseline (median + scaled MAD) and sends a Pushover alert
when a metric stays deviant for several samples. Also alerts on crashed or
restarted containers. Collects silently until 24h of history exist.
"""
import json
import os
import re
import sqlite3
import statistics
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

STATE_DIR = os.path.expanduser("~/.local/state/resource-monitor")
DB = os.path.join(STATE_DIR, "samples.db")
ENV_FILE = os.path.expanduser("~/.config/vuln-monitor/pushover.env")

RETENTION_DAYS = 30
BASELINE_DAYS = 7
MIN_HISTORY_S = 24 * 3600
MIN_BASELINE_POINTS = 200
CONSECUTIVE = 3
RECENT_WINDOW_S = 20 * 60
COOLDOWN_S = 6 * 3600
MAD_K = 4

# metric -> (column, label, unit formatter, min absolute increase, min relative increase)
METRICS = {
    "cpu": ("cpu", "CPU", lambda v: f"{v:.1f}%", 20.0, 0.0),
    "mem": ("mem", "memory", lambda v: f"{v / 1e6:.0f} MB", 50e6, 0.25),
    "net": ("net_bps", "network", lambda v: f"{v / 1e3:.0f} kB/s", 1e6, 0.5),
    "disk": ("disk_bps", "disk I/O", lambda v: f"{v / 1e3:.0f} kB/s", 5e6, 0.5),
}

UNITS = {"B": 1, "kB": 1e3, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12,
         "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3, "TiB": 1024**4}


def log(msg):
    print(f"{datetime.now().isoformat(timespec='seconds')} {msg}", flush=True)


def load_env():
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("\"'")
    return env


def notify(env, title, message, priority):
    data = urllib.parse.urlencode({
        "token": env["PUSHOVER_TOKEN"], "user": env["PUSHOVER_USER"],
        "title": title[:250], "message": message[:1024], "priority": priority,
    }).encode()
    urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=30).read()


def size(s):
    m = re.fullmatch(r"\s*([\d.]+)\s*([A-Za-z]*)\s*", s)
    return float(m.group(1)) * UNITS.get(m.group(2) or "B", 1) if m else 0.0


def pair(s):
    a, _, b = s.partition("/")
    return size(a), size(b)


def docker(*args):
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=True).stdout


def collect():
    rows = []
    for line in docker("stats", "--no-stream", "--format", "{{json .}}").splitlines():
        d = json.loads(line)
        mem, limit = pair(d["MemUsage"])
        rx, tx = pair(d["NetIO"])
        br, bw = pair(d["BlockIO"])
        rows.append({"name": d["Name"], "cpu": float(d["CPUPerc"].rstrip("%") or 0),
                     "mem": mem, "mem_limit": limit, "net": rx + tx, "blk": br + bw})
    started = {}
    names = [r["name"] for r in rows]
    if names:
        for line in docker("inspect", "-f", "{{.Name}} {{.State.StartedAt}}", *names).splitlines():
            n, _, s = line.partition(" ")
            started[n.lstrip("/")] = s
    for r in rows:
        r["started"] = started.get(r["name"], "")
    return rows


def init(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS samples (
            ts INTEGER, name TEXT, cpu REAL, mem REAL, mem_limit REAL,
            net_total REAL, blk_total REAL, net_bps REAL, disk_bps REAL, started TEXT);
        CREATE INDEX IF NOT EXISTS samples_idx ON samples (name, ts);
        CREATE TABLE IF NOT EXISTS alerts (name TEXT, kind TEXT, ts INTEGER);
    """)


def store(db, now, rows):
    for r in rows:
        prev = db.execute("SELECT ts, net_total, blk_total, started FROM samples "
                          "WHERE name=? ORDER BY ts DESC LIMIT 1", (r["name"],)).fetchone()
        r["net_bps"] = r["disk_bps"] = None
        r["restarted"] = bool(prev and prev[3] and r["started"] != prev[3])
        if prev and not r["restarted"] and now > prev[0]:
            dt = now - prev[0]
            if r["net"] >= prev[1]:
                r["net_bps"] = (r["net"] - prev[1]) / dt
            if r["blk"] >= prev[2]:
                r["disk_bps"] = (r["blk"] - prev[2]) / dt
        db.execute("INSERT INTO samples VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (now, r["name"], r["cpu"], r["mem"], r["mem_limit"], r["net"], r["blk"],
                    r["net_bps"], r["disk_bps"], r["started"]))
    db.execute("DELETE FROM samples WHERE ts < ?", (now - RETENTION_DAYS * 86400,))
    db.execute("DELETE FROM alerts WHERE ts < ?", (now - 2 * COOLDOWN_S,))
    db.commit()


def cooled_down(db, now, name, kind):
    row = db.execute("SELECT MAX(ts) FROM alerts WHERE name=? AND kind=?", (name, kind)).fetchone()
    return not row[0] or now - row[0] >= COOLDOWN_S


def deviations(db, now, name):
    out = []
    first = db.execute("SELECT MIN(ts) FROM samples WHERE name=?", (name,)).fetchone()[0]
    if not first or now - first < MIN_HISTORY_S:
        return out
    for key, (col, label, fmt, min_abs, min_rel) in METRICS.items():
        base = [v for (v,) in db.execute(
            f"SELECT {col} FROM samples WHERE name=? AND ts BETWEEN ? AND ? AND {col} IS NOT NULL",
            (name, now - BASELINE_DAYS * 86400, now - RECENT_WINDOW_S))]
        if len(base) < MIN_BASELINE_POINTS:
            continue
        med = statistics.median(base)
        mad = statistics.median(abs(v - med) for v in base) * 1.4826
        limit = med + MAD_K * mad
        recent = [v for (v,) in db.execute(
            f"SELECT {col} FROM samples WHERE name=? AND ts >= ? AND {col} IS NOT NULL "
            f"ORDER BY ts DESC LIMIT ?", (name, now - RECENT_WINDOW_S, CONSECUTIVE))]
        if len(recent) < CONSECUTIVE:
            continue
        if all(v > limit and v - med >= min_abs and v - med >= min_rel * med for v in recent):
            out.append((key, f"{label} {fmt(recent[0])} (baseline {fmt(med)})"))
    return out


def main():
    os.makedirs(STATE_DIR, exist_ok=True)
    db = sqlite3.connect(DB)
    init(db)
    now = int(time.time())

    prev_ts = db.execute("SELECT MAX(ts) FROM samples").fetchone()[0]
    prev_names = {n for (n,) in db.execute("SELECT name FROM samples WHERE ts=?", (prev_ts,))} if prev_ts else set()

    rows = collect()
    store(db, now, rows)
    running = {r["name"] for r in rows}
    log(f"sampled {len(rows)} containers")

    alerts = []  # (name, kind, text, priority)
    for r in rows:
        if r["restarted"]:
            alerts.append((r["name"], "restart", "restarted", 0))
        for key, text in deviations(db, now, r["name"]):
            high = key == "mem" and r["mem_limit"] and r["mem"] / r["mem_limit"] > 0.9
            alerts.append((r["name"], key, text, 1 if high else 0))
    for name in prev_names - running:
        try:
            code = int(docker("inspect", "-f", "{{.State.ExitCode}}", name).strip())
        except subprocess.CalledProcessError:
            code = None  # container removed
        if code != 0:
            alerts.append((name, "gone", "no longer running" + (f" (exit {code})" if code else " (removed)"), 1))

    alerts = [a for a in alerts if cooled_down(db, now, a[0], a[1])]
    if not alerts:
        return
    lines = [f"{n}: {t}" for n, _, t, _ in alerts]
    log("alerts: " + "; ".join(lines))
    notify(load_env(), f"docker: {len(alerts)} resource alert(s)", "\n".join(lines),
           max(a[3] for a in alerts))
    db.executemany("INSERT INTO alerts VALUES (?,?,?)", [(n, k, now) for n, k, _, _ in alerts])
    db.commit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e!r}")
        sys.exit(1)
