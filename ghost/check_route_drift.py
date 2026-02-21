#!/usr/bin/env python3
"""
Route drift checker: verifies Caddyfile routes match SECURITY_REVIEW.md documentation.

Parses the Caddyfile for exposed path patterns and compares against the route
inventory in SECURITY_REVIEW.md. Reports any routes that are exposed but
undocumented, or documented but not exposed.

Usage:
    python check_route_drift.py
    python check_route_drift.py --caddyfile ./Caddyfile --security-review ./SECURITY_REVIEW.md
"""

import argparse
import re
import sys
from pathlib import Path


def parse_caddyfile_routes(caddyfile_path: str) -> set[str]:
    """Extract exposed route paths from Caddyfile matchers.

    Looks for 'path' directives inside named matchers (@name { path ... })
    and returns a set of path patterns.
    """
    content = Path(caddyfile_path).read_text()
    routes = set()

    # Match path directives inside named matchers
    # Pattern: path /some/route or path /route1 /route2
    path_pattern = re.compile(r'^\s+path\s+(.+)$', re.MULTILINE)
    path_regexp_pattern = re.compile(r'^\s+path_regexp\s+\S*\s*(.+)$', re.MULTILINE)

    for match in path_pattern.finditer(content):
        paths = match.group(1).strip()
        for p in paths.split():
            # Normalize: strip trailing wildcard for comparison
            normalized = p.rstrip("*").rstrip("/")
            if normalized:
                routes.add(normalized)

    for match in path_regexp_pattern.finditer(content):
        regexp = match.group(1).strip()
        # Extract the base path from simple regexes like ^/\.ghost/analytics/
        base_match = re.match(r'\^?(/[a-zA-Z0-9._/-]+)', regexp)
        if base_match:
            routes.add(base_match.group(1).rstrip("/"))

    return routes


def parse_security_review_routes(review_path: str) -> set[str]:
    """Extract documented route paths from SECURITY_REVIEW.md.

    Looks for route patterns in the markdown document:
    - Bullet points like "- `GET /api/interactions/*`"
    - Table cells like "| `/api/interactions/*` |"
    """
    content = Path(review_path).read_text()
    routes = set()

    # Match bullet-point routes: - `GET /some/path`  or  - `POST /some/path`
    bullet_pattern = re.compile(r'`(?:GET|POST|OPTIONS|PUT|DELETE|PATCH)\s+(/[^\s`]+)`')
    for match in bullet_pattern.finditer(content):
        path = match.group(1).rstrip("*").rstrip("/")
        if path:
            routes.add(path)

    # Match table routes: | `/some/path` |
    table_pattern = re.compile(r'\|\s*`(/[^\s`]+)`\s*\|')
    for match in table_pattern.finditer(content):
        path = match.group(1).rstrip("*").rstrip("/")
        if path:
            routes.add(path)

    return routes


def main():
    parser = argparse.ArgumentParser(description="Check for route drift between Caddyfile and SECURITY_REVIEW.md")
    script_dir = Path(__file__).parent
    parser.add_argument("--caddyfile", default=str(script_dir / "Caddyfile"), help="Path to Caddyfile")
    parser.add_argument("--security-review", default=str(script_dir / "SECURITY_REVIEW.md"), help="Path to SECURITY_REVIEW.md")
    args = parser.parse_args()

    caddy_routes = parse_caddyfile_routes(args.caddyfile)
    doc_routes = parse_security_review_routes(args.security_review)

    exposed_but_undocumented = caddy_routes - doc_routes
    documented_but_not_exposed = doc_routes - caddy_routes

    exit_code = 0

    if exposed_but_undocumented:
        print("DRIFT: Routes exposed in Caddyfile but NOT documented in SECURITY_REVIEW.md:")
        for route in sorted(exposed_but_undocumented):
            print(f"  - {route}")
        exit_code = 1

    if documented_but_not_exposed:
        print("DRIFT: Routes documented in SECURITY_REVIEW.md but NOT found in Caddyfile:")
        for route in sorted(documented_but_not_exposed):
            print(f"  - {route}")
        exit_code = 1

    if exit_code == 0:
        print(f"OK: All {len(caddy_routes)} Caddyfile routes are documented ({len(doc_routes)} documented routes found).")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
