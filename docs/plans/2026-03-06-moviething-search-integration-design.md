# Replace OMDB with Moviething Search Backend

## Problem

The snfc-posting-tool and moviething both implement movie searching independently.
The snfc-posting-tool uses OMDB; moviething uses TMDB with richer filtering (popularity,
vote count, vote average, release date range). Maintaining two separate search
implementations is redundant.

## Decision

Standardize on moviething as the single movie search backend. The snfc-posting-tool
will proxy search requests to moviething over a shared Docker network.

## Architecture

```
Browser -> Authentik -> snfc-posting-tool (Flask)
                             | (Docker network, forwarding x-authentik-username)
                             v
                        moviething (Express)
```

The Flask backend acts as a thin proxy, translating moviething's TMDB-based responses
into the shape the snfc-posting-tool frontend expects.

## Backend Changes (app.py)

### New config field

Add `moviething.baseUrl` to config.json (e.g., `http://moviething:3000/api`).

### New endpoints

- `GET /api/movie/search?q=<title>&exclude_videos=...&min_popularity=...` etc.
  - POSTs to `moviething/api/searchMovie` with JSON body containing title and filter params
  - Forwards `x-authentik-username` header from the original request
  - Translates response to `{Search: [{Title, Year, tmdbID, Poster}], Response: "True"}`

- `GET /api/movie/details?id=<tmdbID>`
  - POSTs to `moviething/api/getMovieDetails` with `{tmdbID}`
  - Forwards `x-authentik-username` header
  - Translates response to `{Title, imdbID, Plot, Response: "True"}`

### Removed endpoints

- `/api/omdb/search`
- `/api/omdb/movie`

### Removed config

- `omdb` section from config.json / config.example.json

## Frontend Changes (main.js)

### Search

- Update AJAX calls from `/api/omdb/search` to `/api/movie/search`
- Update movie selection from `/api/omdb/movie` to `/api/movie/details`
- Use `tmdbID` instead of `imdbID` as the result identifier
- On selection, still populate: film title, `https://www.imdb.com/title/<imdbID>/`, plot

### Filter UI

Add a collapsible filter panel (disclosure triangle / `<details>` element) with:
- Exclude videos (checkbox)
- Popularity range (min/max number inputs)
- Vote count range (min/max number inputs)
- Vote average range (min/max number inputs)
- Release date range (min/max date inputs)

Filter values are sent as query params with each search request. Filters persist in
the panel state but are not saved to localStorage (unlike moviething's add page).

### Results display

Same as current: dropdown list of "Title (Year)" items. Clicking a result populates
the form fields.

## Config Changes

### config.example.json

Remove:
```json
"omdb": {
    "apiKey": "YOUR_OMDB_API_KEY"
}
```

Add:
```json
"moviething": {
    "baseUrl": "http://moviething:3000/api"
}
```

## Infrastructure

- Create a shared Docker network between snfc-posting-tool and moviething compose stacks
- Both compose files reference the shared external network
- No new containers or services needed

## Error Handling

- If moviething is unreachable, return `{Search: [], error: "Movie search unavailable"}`
  so the frontend can display the message inline
- No OMDB fallback

## Data Flow

1. User types in search box (>= 2 chars)
2. JS debounces (300ms), sends GET to `/api/movie/search?q=...&filters...`
3. Flask proxy POSTs to `moviething:3000/api/searchMovie` with JSON body, forwarding Authentik header
4. Response translated to `{Search: [{Title, Year, tmdbID, Poster}], Response: "True"}`
5. User clicks a result
6. JS sends GET to `/api/movie/details?id=<tmdbID>`
7. Flask proxy POSTs to `moviething:3000/api/getMovieDetails`, forwards Authentik header
8. Response translated to `{Title, imdbID, Plot}`
9. Form fields populated: film title, IMDB URL, plot synopsis
