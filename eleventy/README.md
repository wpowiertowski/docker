# eleventy

Example Dockerized [11ty](https://www.11ty.dev/) static site with Ghost-inspired styling.

## Run

```bash
cd eleventy
docker compose -f compose.yml up --build -d
```

Open http://localhost:8080.

## Customize

- Content: `src/`
- Global layout: `src/_includes/layout.njk`
- Styles: `src/css/site.css`
