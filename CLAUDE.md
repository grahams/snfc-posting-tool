# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sunday Night Film Club (SNFC) posting tool — a Flask web app that lets film club hosts compose a weekly newsletter and publish it to multiple services simultaneously via a plugin system.

## Running Locally

```bash
pip install -r requirements.txt
cp config.example.json config.json  # then edit with your values
python app.py                       # Flask dev server on port 5000
```

CLI test tool for invoking plugins directly:
```bash
python testtool.py --help
python testtool.py --plugin "SNFC Mailing List" --film "Example" --time 7:30pm
```

Production runs via gunicorn on port 8000 (see Dockerfile).

## Architecture

### Request Flow

`Browser -> Authentik (auth proxy) -> Flask app (app.py) -> plugins`

The form at `/` collects film details, renders a live newsletter preview, and on submit dispatches to selected plugins. The app also proxies movie search requests to a separate **moviething** service over a shared Docker network.

### Core Components

- **`app.py`** — Flask routes: form rendering, newsletter preview (`/api/preview`), movie search proxy (`/api/movie/search`, `/api/movie/details`), and form submission that dispatches to plugins.
- **`Newsletter.py`** — Builds newsletter content (HTML via Jinja2 template, subject line, short text for social posts, plain text, markdown). Handles time normalization and date calculation (next Sunday).
- **`BasePostingAction.py`** — Base class for plugins. Subclasses must set `pluginName`, `configSection`, and implement `execute(config, nl)`.

### Plugin System

Plugins live in `plugins/` and are dynamically loaded by class name matching filename. Each plugin:
- Extends `BasePostingAction`
- Sets `pluginName` (display name) and `configSection` (key in config.json)
- Implements `execute(config, nl)` receiving the full config dict and a `Newsletter` instance
- Can be enabled/disabled via `config[configSection].enabled`

Current plugins: Bluesky, Mastodon, Mailing List, Hugo, Google Calendar.

### Movie Search Proxy

The app proxies search requests to the **moviething** service (a separate Node.js/Express app using TMDB API):
- `/api/movie/search` -> moviething's `/api/searchMovie` (with TMDB filter support)
- `/api/movie/details` -> moviething's `/api/getMovieDetails`
- Forwards `x-authentik-username` header for auth
- Uses form-encoded POST with `data={'json': json.dumps(payload)}` — this is intentional, matching moviething's Express `urlencoded` parsing

### Frontend

jQuery-based (`static/js/main.js`). Key features:
- Movie search with typeahead dropdown (uses TMDB via moviething proxy)
- Collapsible advanced search filters (`<details>` element)
- Live newsletter preview in iframe via `/api/preview`
- Manual HTML editing mode with rich text toolbar
- AJAX form submission with per-plugin status indicators

### Config

`config.json` (not committed) contains: club info, hosts, locations, moviething baseUrl, and per-plugin credentials. See `config.example.json` for structure.

## Deployment

- Pushes to `main` trigger GitHub Actions to build and push Docker image to `ghcr.io/grahams/snfc-posting-tool:latest`
- Deployed via Docker Compose behind Traefik reverse proxy with Authentik for auth
- Multiple instances can run for different cities (each with its own config.json volume mount)
- Shared `moviething` Docker network connects to the moviething service

## No Test Suite

This project does not currently have automated tests.
