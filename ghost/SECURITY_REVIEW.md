# Ghost + Caddy + POSSE Security Review (Caddy exposure + POSSE endpoint handling)

Date: 2026-02-07
Last validated against: Caddyfile and POSSE source on 2026-02-20

## Scope

This review focuses on:

1. Caddy edge configuration in `ghost/Caddyfile`.
2. The set of endpoints exposed from Caddy to POSSE.
3. How those exposed endpoints are handled in POSSE code.

### Important limitation

I could not fetch the external POSSE repository (`https://github.com/wpowiertowski/posse`) from this execution environment (network request to GitHub failed with HTTP 403 via the proxy tunnel). This means POSSE findings below are based on the existing local deployment documentation and configuration, not a fresh source-code audit of the upstream repository.

---

## Caddy exposure analysis

### What is publicly exposed

Caddy is default-deny with explicit route allowlisting. The following routes are exposed to the internet:

- `GET /api/interactions/*`
- `OPTIONS /api/interactions/*`
- `GET /api/webmentions`
- `OPTIONS /api/webmentions`
- `GET /webmention` (reply form)
- `POST /webmention` (W3C receiver, `application/x-www-form-urlencoded` only)
- `OPTIONS /webmention`
- `POST /api/webmention/reply` (`application/json` only)
- `OPTIONS /api/webmention/reply`
- `GET /reply/*`

Global `Link: </webmention>; rel="webmention"` header is set on all responses for W3C webmention endpoint discovery.

All other paths return `404`.

### Existing strong controls

- Global Caddy admin API disabled (`admin off`).
- Read/write/idle/header timeouts are configured.
- A suspicious path regex blocks obvious traversal and poison patterns (`..`, `%2e%2e`, `%00`, `%0a`, `%0d`).
- Response hardening headers are set (frame deny, nosniff, referrer policy, CSP, server header removal).
- Request body limits are present:
  - `1KB` for read-only or preflight endpoints.
  - `16KB` for webmention reply submission.
- Reverse proxy forwards expected upstream context (`Host`, `X-Forwarded-Proto=https`, Cloudflare IP header mapping).

### Caddy risks and recommendations

#### 1) Medium: OPTIONS routes do not forward standardized forwarding headers

For OPTIONS handlers, Caddy uses `reverse_proxy ghost-posse:5000` without the explicit `header_up` directives used in GET/POST handlers. If POSSE applies origin, scheme, or IP-based decisions for preflight handling, behavior can diverge between OPTIONS and non-OPTIONS requests.

**Recommendation:** Add identical `header_up` settings for OPTIONS handlers to keep request semantics consistent.

#### 2) Medium: Trusting `Cf-Connecting-Ip` without strict provenance validation

Caddy sets `X-Real-IP` and `X-Forwarded-For` from `Cf-Connecting-Ip`. This is correct when all inbound traffic is guaranteed to come from Cloudflare Tunnel. Risk appears if any bypass path to Caddy exists now or later.

**Recommendation:**
- Keep Caddy unreachable except through the tunnel network path.
- Document and periodically test that no host port or alternate ingress path exposes Caddy directly.

#### 3) Low: Legacy header `X-XSS-Protection`

`X-XSS-Protection` is legacy/ignored by modern browsers and can be removed to simplify policy surface.

**Recommendation:** Optional cleanup; keep CSP as the primary browser-side control.

---

## Endpoint-by-endpoint security view

| Endpoint | Method(s) | Exposure purpose | Current safeguards | Residual risk |
|---|---|---|---|---|
| `/api/interactions/*` | GET, OPTIONS | Public interaction lookups | Body limit, CSP, default-deny routing, traversal filter | Upstream handling quality and rate limits define abuse ceiling |
| `/api/webmentions` | GET, OPTIONS | Public webmention query | 1KB body limit, CSP, rate limiting, referrer validation | Query only returns verified webmentions; rate limits bound abuse |
| `/webmention` | GET, POST, OPTIONS | Reply form (GET) + W3C receiver (POST) | 4KB body limit for POST, CSP with Turnstile for GET, rate limiting, SSRF protection | Source URL fetching during async verification; receiver rate-limited per IP |
| `/api/webmention/reply` | POST, OPTIONS | Reply submission | 16KB body cap, security headers, default-deny routing | Abuse pressure depends on POSSE anti-automation (captcha/token/rate limiting) |
| `/reply/*` | GET | Reply resource view | CSP + body cap + traversal filter | Content rendering safety in POSSE determines XSS exposure |

---

## POSSE handling review (from local deployment documentation)

Based on the existing local review and deployment context, POSSE is expected to implement:

- Strict input validation (including post-ID shape checks).
- Rate limiting at multiple levels (per-IP and endpoint-specific windows).
- Constant-time token comparison for internal auth (`hmac.compare_digest`).
- Parameterized SQL usage.
- CORS disabled by default unless explicitly allowed.
- Secret loading via Docker secrets, not plaintext environment variables.

Because upstream source code could not be fetched in this environment, treat these as **assumed controls requiring independent verification** against the exact deployed image digest.

---

## Deployment-level observations impacting POSSE security

### 1) Image mutability remains the largest practical supply-chain risk

`ghost-posse` uses `wpowiertowski/posse:latest` with Watchtower updates enabled. This can introduce unreviewed behavior changes in publicly exposed handlers.

**Recommendation (High priority):** Pin POSSE image by immutable digest and promote updates through explicit review.

### 2) Public attack surface is intentionally narrow and generally well constrained

The Caddy policy is close to a strong minimal-exposure model: explicit route allowlist, default 404, tight headers, body limits, and proxy isolation from Ghost/MySQL.

**Recommendation:** Keep this allowlist discipline. Any new endpoint should be threat-reviewed before exposure.

### 3) Cross-network bridge role of POSSE is a critical trust boundary

POSSE is the only service bridging `proxy` and `ghost` networks, making it the primary pivot point if compromised.

**Recommendation:**
- Keep privilege restrictions (`no-new-privileges`, dropped capabilities, read-only root where possible).
- Monitor POSSE logs for anomalous request spikes/path probes.
- Consider adding network egress restrictions if your runtime supports them.

---

## Priority action list

1. **Pin `ghost-posse` image by digest** and avoid `:latest` in production.
2. **Normalize forwarding headers for OPTIONS** handlers in Caddy.
3. **Verify no direct ingress path to Caddy** exists outside Cloudflare Tunnel.
4. **Perform source-level POSSE audit** against the exact deployed commit/image when GitHub access is available.
