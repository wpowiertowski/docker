---
layout: layout.njk
title: Getting Started with 11ty in Docker
---

# Getting Started with 11ty in Docker

You can run this example with:

```bash
docker compose -f compose.yml up --build -d
```

Then open `http://localhost:8080`.

## Why this setup?

- **Eleventy** builds HTML from markdown and templates.
- **Nginx** serves the generated static files efficiently.
- **Docker** keeps the whole workflow reproducible.
