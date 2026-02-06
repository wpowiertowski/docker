# Ghost + POSSE public-web threat review

This review focuses on abuse paths from the public internet for the `ghost` Docker/Caddy deployment and POSSE integration.

## Current architecture (as deployed here)

- Public traffic enters via **Cloudflare Tunnel** and reaches `ghost-caddy`.
- `ghost-caddy` only proxies `GET` and `OPTIONS` for `/api/interactions/*` to `ghost-posse`.
- `ghost-posse` has access to social-network and Ghost API secrets via Docker secrets.
- Ghost and MySQL are private to the `ghost` Docker network.

## Key abuse scenarios and mitigations

### 1. Host header / origin confusion through reverse proxy

**Threat**
An attacker can abuse inconsistent upstream forwarding to influence backend-generated absolute URLs, cache keys, redirects, or origin logic.

**Mitigation implemented**
- Explicitly forward canonical `Host` from Caddy to POSSE backend with `header_up Host {host}`.

**Why it is low-risk for functionality**
- Keeps existing route/method behavior unchanged.
- Only standardizes what host header the backend sees.

### 2. Unnecessary admin surface on edge proxy

**Threat**
Caddy's admin endpoint should not be exposed in production. Even if not intentionally published, hard-disabling reduces accidental control-plane exposure.

**Mitigation implemented**
- Set `admin off` in the Caddyfile.

**Why it is low-risk for functionality**
- This stack does not rely on Caddy's dynamic runtime API.
- Static Caddyfile operation remains unchanged.

### 3. Container breakout blast radius (public-facing services)

**Threat**
If a public-facing process is compromised (e.g., Caddy or POSSE endpoint bug), Linux privilege escalation opportunities increase if containers can gain extra privileges.

**Mitigation implemented**
- Added `security_opt: ["no-new-privileges:true"]` to:
  - `ghost-posse`
  - `ghost-caddy`
  - `ghost-caddy-tunnel`

**Why it is low-risk for functionality**
- Prevents privilege escalation via `setuid`/`setgid` binaries while preserving normal runtime behavior.
- No changes to ports, routes, secrets, or volumes.


### 4. Scheme confusion behind Cloudflare Tunnel

**Threat**
When Caddy is reached via cloudflared over internal HTTP, forwarding `X-Forwarded-Proto` based on local connection scheme can incorrectly report `http` to POSSE. This can affect URL generation, origin checks, and downstream security logic.

**Mitigation implemented**
- Explicitly set `X-Forwarded-Proto https` for POSSE upstream requests in Caddy.

**Why it is low-risk for functionality**
- Public traffic is HTTPS at Cloudflare edge; this reflects real client-facing scheme.
- Does not change route/method filtering or API exposure.

## Additional recommended hardening (not changed yet)

1. Pin images by digest (`image: repo@sha256:...`) for `ghost`, `mysql`, `caddy`, `cloudflared`, and `posse` to reduce supply-chain drift.
2. Add resource controls (`mem_limit`, CPU limits) on public-facing services to reduce DoS blast radius.
3. Keep Caddy access logs, and add alerting on high-rate 403/404 and path traversal signatures.
4. Restrict egress for services that do not need broad outbound internet (where runtime platform supports it).
5. Periodically rotate Docker secrets used by POSSE social integrations and Ghost keys.

## POSSE built-in security measures considered

From this repo's integration perspective:
- POSSE API exposure is constrained to a read-only style route shape (`GET /api/interactions/*`) with explicit method filtering at Caddy.
- CORS preflight is delegated to POSSE, while non-allowed methods and paths are denied at proxy.
- Sensitive credentials are injected as Docker secrets rather than plain environment variables.

(Deeper application-layer validation/rate-limit behavior inside POSSE code should be verified in the POSSE repository itself.)
