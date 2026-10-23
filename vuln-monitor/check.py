#!/usr/bin/env python3
"""Daily check of running Docker containers against new pwn.watch incidents.

Sends a Pushover notification for incidents not reported before whose
slug/title/product/tags mention a keyword derived from a running image.
The first run records the current backlog silently.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime

FEED = "https://pwn.watch/incidents.json"
STATE_DIR = os.path.expanduser("~/.local/state/vuln-monitor")
SEEN = os.path.join(STATE_DIR, "seen.json")
LOG = os.path.join(STATE_DIR, "matches.log")
ENV_FILE = os.path.expanduser("~/.config/vuln-monitor/pushover.env")

# Keywords added on top of those derived from image names.
EXTRA = {
    "ghost": ["nodejs", "node.js"],
    "cloudflared": ["cloudflare"],
    "mysql": ["mysql"],
    "nginx": ["nginx"],
}
IGNORE = {"latest", "stable", "alpine", "backup", "docker", "web", "server"}


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


def running_images():
    out = subprocess.run(
        ["docker", "ps", "--format", "{{.Image}}"],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    return sorted(set(out))


def keywords(images):
    kws = set()
    for img in images:
        if re.fullmatch(r"[0-9a-f]{12,64}", img):
            continue  # untagged local image id
        name = img.split("@")[0].rsplit(":", 1)[0]
        parts = name.split("/")
        base = parts[-1]
        for p in (base, name.split("/", 1)[-1] if len(parts) > 1 else base):
            if p and p not in IGNORE:
                kws.add(p.lower())
        for key, extra in EXTRA.items():
            if key in name:
                kws.update(extra)
    return kws


def matches(incident, kws):
    hay = " ".join(
        [incident.get("slug", ""), incident.get("title", ""), incident.get("product", "")]
        + incident.get("tags", [])
    ).lower().replace("-", " ")
    return sorted(k for k in kws if re.search(rf"\b{re.escape(k.replace('-', ' '))}\b", hay))


def notify(env, title, message, priority):
    data = urllib.parse.urlencode({
        "token": env["PUSHOVER_TOKEN"],
        "user": env["PUSHOVER_USER"],
        "title": title[:250],
        "message": message[:1024],
        "priority": priority,
    }).encode()
    urllib.request.urlopen("https://api.pushover.net/1/messages.json", data, timeout=30).read()


def main():
    os.makedirs(STATE_DIR, exist_ok=True)
    kws = keywords(running_images())
    log(f"keywords: {sorted(kws)}")

    req = urllib.request.Request(FEED, headers={"User-Agent": "vuln-monitor/1.0 (+docker)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        incidents = json.load(r)["incidents"]

    first_run = not os.path.exists(SEEN)
    seen = set() if first_run else set(json.load(open(SEEN)))
    new = [i for i in incidents if i["slug"] not in seen]

    hits = []
    if not first_run:
        for i in new:
            if i.get("closedAt"):
                continue
            m = matches(i, kws)
            if m:
                hits.append((i, m))

    with open(SEEN, "w") as f:
        json.dump(sorted(seen | {i["slug"] for i in incidents}), f)

    if first_run:
        log(f"first run: recorded {len(incidents)} incidents, no alerts")
        return
    if not hits:
        log(f"{len(new)} new incidents, none relevant")
        return

    lines, urgent = [], False
    for i, m in hits:
        sev = i.get("severity", "unrated")
        patch = i.get("patchStatus", "?")
        urgent |= sev == "critical" or patch == "none"
        lines.append(f"[{sev}/{patch}] {i['title']} ({', '.join(m)})\n{i['url']}")
    with open(LOG, "a") as f:
        for l in lines:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {l}\n")
    log(f"{len(hits)} relevant incidents")
    notify(load_env(), f"pwn.watch: {len(hits)} incident(s) match your containers",
           "\n\n".join(lines), 1 if urgent else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e!r}")
        sys.exit(1)
