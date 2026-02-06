# Ghost + POSSE public-web threat review

This review focuses on abuse paths from the public internet for the `ghost` Docker/Caddy deployment and POSSE integration. Insider threats are out of scope.

## Current architecture (as deployed here)

```
Internet
  |
  +--[CF Tunnel 1 (ghost-tunnel)]-------> ghost-server:2368 (Ghost blog)
  |                                              |
  |                                        ghost-db (MySQL 8)
  |
  +--[CF Tunnel 2 (ghost-caddy-tunnel)]--> ghost-caddy:80 (Caddy)
        [proxy network]                        |
                                          ghost-posse:5000
                                          [proxy + ghost networks]
```

- Public traffic enters via **Cloudflare Tunnel** and reaches either Ghost or `ghost-caddy`.
- `ghost-caddy` only proxies `GET` and `OPTIONS` for `/api/interactions/*` to `ghost-posse`.
- `ghost-posse` has access to social-network and Ghost API secrets via Docker secrets.
- Ghost and MySQL are private to the `ghost` Docker network.
- Caddy and its tunnel are isolated on a separate `proxy` network; only POSSE bridges both.

## Threat model: key abuse scenarios and mitigations

### 1. Lateral movement via flat Docker network

**Threat**
All containers on a single shared network means a compromised Caddy or POSSE process can reach Ghost admin, MySQL, the backup agent, and every other container directly. An attacker exploiting a vulnerability in the public-facing proxy chain gains access to the entire backend.

**Mitigation implemented**
- Split into two networks: `proxy` (Caddy + tunnel + POSSE) and `ghost` (Ghost + MySQL + tunnel + POSSE + backup).
- Caddy and its Cloudflare tunnel can **only** reach POSSE, not Ghost or MySQL.
- POSSE bridges both networks because it needs Caddy inbound and Ghost Content API outbound.

**Why it preserves functionality**
- Caddy still proxies to `ghost-posse:5000` over the `proxy` network.
- POSSE still reaches `ghost-server` for content API reads over the `ghost` network.
- Ghost tunnel still reaches `ghost-server` over the `ghost` network.

### 2. Resource exhaustion / DoS against public endpoints

**Threat**
Without memory or CPU limits, an attacker flooding the POSSE API through Cloudflare can cause Caddy or POSSE to consume all host memory/CPU, starving Ghost and MySQL.

**Mitigation implemented**
- `mem_limit` and `cpus` on all three public-facing containers:
  - `ghost-caddy`: 128 MB / 0.5 CPU
  - `ghost-caddy-tunnel`: 128 MB / 0.5 CPU
  - `ghost-posse`: 256 MB / 0.5 CPU
- Caddy server-level timeouts to mitigate slowloris and connection exhaustion:
  - `read_header`: 5s, `read_body`: 10s, `write`: 30s, `idle`: 60s
- Request body size capped at 1 KB (GET/OPTIONS endpoints carry no body).

**Why it preserves functionality**
- These limits are generous for the actual workload (JSON API responses, lightweight proxy).
- Timeouts are well above normal request latency.

### 3. Container privilege escalation

**Threat**
If an attacker gains code execution inside a container (e.g., via a dependency vulnerability), they can escalate privileges using setuid/setgid binaries or Linux capabilities.

**Mitigation implemented**
- `security_opt: ["no-new-privileges:true"]` on **all 7 containers** (previously only 3).
- `cap_drop: [ALL]` on public-facing containers (Caddy, tunnel, POSSE) to drop all Linux capabilities.
- `cap_add: [NET_BIND_SERVICE]` only on Caddy (needs port 80 binding).
- `read_only: true` root filesystem on Caddy, its tunnel, and POSSE — prevents writing to the container filesystem.
- `tmpfs` mounts at `/tmp` with `noexec,nosuid` for ephemeral scratch space.

**Why it preserves functionality**
- Caddy writes persistent data to `/data` and `/config` volumes (unaffected by read-only root).
- POSSE writes to `/app/data` volume (unaffected).
- No setuid binaries or extra capabilities are needed at runtime.

### 4. Host header / origin confusion through reverse proxy

**Threat**
An attacker can abuse inconsistent upstream forwarding to influence backend-generated absolute URLs, cache keys, redirects, or origin logic.

**Mitigation implemented**
- Explicitly forward canonical `Host` from Caddy to POSSE backend with `header_up Host {host}`.

### 5. Unnecessary admin surface on edge proxy

**Threat**
Caddy's admin endpoint should not be exposed in production. Even if not intentionally published, hard-disabling reduces accidental control-plane exposure.

**Mitigation implemented**
- Set `admin off` in Caddy global options.

### 6. Scheme confusion behind Cloudflare Tunnel

**Threat**
When Caddy is reached via cloudflared over internal HTTP, forwarding `X-Forwarded-Proto` based on local connection scheme can incorrectly report `http` to POSSE. This can affect URL generation, origin checks, and downstream security logic.

**Mitigation implemented**
- Explicitly set `X-Forwarded-Proto https` for POSSE upstream requests in Caddy.

### 7. Oversized or malformed request payloads

**Threat**
An attacker sends large request bodies or crafted payloads to exhaust memory or exploit parsing bugs.

**Mitigation implemented**
- Caddy `request_body { max_size 1KB }` — the API only serves GET/OPTIONS with no body.
- Gunicorn (in POSSE) enforces `limit_request_line = 4096`, `limit_request_fields = 100`, `limit_request_field_size = 8190`.

### 8. Path traversal and injection via URL

**Threat**
Encoded path traversal sequences (`../`, `%2e%2e`, null bytes) to escape the allowed path prefix.

**Mitigation implemented**
- Caddy regex blocks `..`, `%2e%2e`, `%252e`, `%00`, `%0a`, `%0d` patterns (returns 403).
- Allowlist routing: only `GET/OPTIONS /api/interactions/*` is proxied; everything else returns 404.
- POSSE validates post IDs as exactly 24-character hex strings and has `is_safe_path()` checks.

## POSSE built-in security measures (defense in depth)

The POSSE application provides additional layers behind Caddy:

| Layer | Measure |
|-------|---------|
| Input validation | JSON Schema (Draft 7), 24-char hex post ID regex, Content-Type enforcement |
| Rate limiting | Per-IP (60 req/60s), per-post discovery cooldown (300s), global discovery limit (50/60s) |
| Auth | Internal API token via `hmac.compare_digest()` (timing-safe) on sync endpoint |
| Referrer validation | Allowlist-based `Referer` header check on interactions API |
| SQL injection | Parameterized queries throughout |
| CORS | Disabled by default; configurable allowlist when enabled |
| Secrets | Docker secrets at `/run/secrets/`, not environment variables |
| Container | Alpine-based, CVE patches (zlib, wget), `PYTHONDONTWRITEBYTECODE=1` |
| YAML | `yaml.safe_load()` prevents deserialization attacks |

## Remaining risks and recommendations

### Docker socket on backup container
The `ghost-backup` container mounts `/var/run/docker.sock:ro` to stop MySQL during snapshots. This grants read access to the full Docker API. The container is not internet-facing and the risk is low, but if compromised it could enumerate containers, read configs, and potentially escalate. Consider switching to a label-based approach with a Docker socket proxy (e.g., `tecnativa/docker-socket-proxy`) that only exposes the container stop/start API.

### Image pinning
All images use floating tags (`:latest`, `:6`, `:8`, `:2-alpine`). Combined with Watchtower auto-updates, a compromised upstream image gets auto-deployed. Pin images by digest (`image: repo@sha256:...`) and update deliberately.

### MySQL root credentials
Ghost connects to MySQL as `root`. Create a dedicated `ghost` MySQL user with only the privileges Ghost needs (`SELECT`, `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `INDEX` on the `ghost` database).

### Ghost webhook signature verification
POSSE does not verify Ghost webhook HMAC-SHA256 signatures. While the sync endpoint requires an internal API token, adding webhook signature verification would provide defense in depth against forged webhook payloads if the token leaks.

### Secret rotation
No automated rotation for Docker secrets (Mastodon tokens, Bluesky passwords, Ghost API keys). Establish a rotation schedule and procedure.
