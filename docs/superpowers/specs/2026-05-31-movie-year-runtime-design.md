# Movie Year & Runtime — Design

Date: 2026-05-31

## Summary

When a film is selected via the moviething/TMDB search, capture its release year and runtime. Append them in parentheses after the film title in the HTML newsletter (e.g., `Backrooms (2026, 110m)`, omitting the year when it matches the current calendar year). Use the runtime to size the Google Calendar event (`runtime + 60m` for post-film dinner padding) instead of the hardcoded 3-hour duration.

## Goals

- Surface year and runtime to newsletter readers without manual lookup.
- Make calendar events accurately reflect the film's actual length.
- Preserve current behavior when no search-backed metadata is available (manually-typed titles, older saved drafts).

## Non-goals

- Year/runtime do NOT appear in the email subject line or short-text social posts (Bluesky/Mastodon). Subject already carries the date; tweets stay terse.
- No retrofitting of historical posts.
- No new data store; the values flow through the existing form-submit path each time.

## User-facing format

`format_film_details(year, runtime, now=datetime.now())` returns the suffix string (including a leading space) appended after the film title:

| year | runtime | current year | output |
| --- | --- | --- | --- |
| 2024 | 110 | 2026 | `" (2024, 110m)"` |
| 2026 | 110 | 2026 | `" (110m)"` |
| 2024 | — | 2026 | `" (2024)"` |
| 2026 | — | 2026 | `""` |
| — | 110 | 2026 | `" (110m)"` |
| — | — | 2026 | `""` |

Implementation notes:
- "Current year" is determined from `nl.get_next_sunday().year` so a Jan-1-Sunday screening of a Dec-released film still reads naturally.
- Runtime is rendered as `<int>m`. If the upstream gives `0` or a non-positive value, treat as missing.
- Year is rendered as a 4-digit string; non-4-digit input is treated as missing.

## Architecture

```
Browser (main.js)
   │  user picks a movie
   ▼
GET /api/movie/details?id=<tmdbID>
   │  proxies to moviething /getMovieDetails
   ▼
app.py extracts {Title, Plot, Year, Runtime}
   │  JSON response
   ▼
main.js writes hidden inputs (filmYear, filmRuntime)
   │
   ├─ POST /api/preview ──► Newsletter(..., year, runtime) ──► htmlnewsletter.html
   │                                                              uses {{ film_details }}
   │
   └─ POST /  ──► Newsletter(..., year, runtime)
                       │
                       └─► GoogleCalendarPostingAction uses nl.runtime + 60m
```

## Component changes

### 1. `app.py` — `/api/movie/details`

Add `Year` and `Runtime` to the returned JSON. Accept any of:
- `Year` (already in search results) OR a 4-digit year parsed from `release_date` / `Released`
- `Runtime` (int) OR `runtime` (int)

Defensive parsing: missing / non-numeric values yield `None`.

### 2. `app.py` — `/api/preview` and `index()` POST

Both accept `filmYear` and `filmRuntime` form/JSON fields and forward them to the `Newsletter` constructor. Empty/invalid values become `None`.

### 3. `Newsletter.py`

- Constructor gains two trailing keyword args: `year: Optional[int] = None`, `runtime: Optional[int] = None`.
- New attributes `self.year` and `self.runtime` (normalized: `None` or positive int).
- New method `format_film_details() -> str` per the table above.
- `generate_HTML()` passes `film_details=self.format_film_details()` to the template.
- Subject and short-text generators are unchanged.

### 4. `templates/htmlnewsletter.html`

```jinja
<a href="{{ filmURL }}">{{ film }}</a>{{ film_details }}
```

The suffix lives outside the `<a>` so the title remains the only clickable text.

### 5. `plugins/GoogleCalendarPostingAction.py`

- Read `nl.runtime`. If set and > 0, total minutes = `runtime + 60`.
- Else fall back to current behavior (`+3` hours).
- Compute end time by adding total minutes to the start `datetime` (replace the brittle `hour + 3` arithmetic that breaks past 9pm anyway).

### 6. `static/js/main.js` and `templates/form.html`

- Add hidden `<input type="hidden" id="filmYear" name="filmYear">` and `id="filmRuntime" name="filmRuntime"`.
- On successful `/api/movie/details`, set both.
- On user keystrokes in `#filmSearch` (the `input` handler), clear both — selecting from the dropdown re-fills them.
- Include both fields in the `/api/preview` payload.

### 7. `testtool.py`

Add `--year` and `--runtime` CLI flags, plumbed into `Newsletter(...)`.

## Edge cases

- **Manual film title (no search)**: hidden fields stay empty; Newsletter receives `None`/`None`; HTML title shows unchanged; calendar falls back to 3h. ✅
- **Stale year/runtime after manual edit**: cleared as soon as the user types in the search box. ✅
- **Manual HTML override mode**: `format_film_details()` not used (override HTML wins). The hidden fields still flow through and the Google Calendar duration still uses runtime if set. ✅
- **moviething returns null/0 runtime** (e.g., unreleased films): treated as missing. ✅
- **End time after midnight**: computed via `timedelta` so a 9pm screening of a 3-hour film correctly produces an event ending the next day in the same timezone.

## Out of scope (deferred)

- Persisting year/runtime in Hugo front matter — possible future enhancement but not requested.
- Showing runtime in calendar event description body.
- Localized runtime formats (e.g., `1h 50m`). `<n>m` is what the user asked for.
