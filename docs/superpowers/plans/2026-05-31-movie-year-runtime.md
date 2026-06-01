# Movie Year & Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display year/runtime after movie titles in the newsletter (e.g., `Backrooms (2026, 110m)`) and size Google Calendar events from runtime + 60m dinner padding.

**Architecture:** Capture `Year` and `Runtime` from the moviething movie-details proxy, persist them through hidden form inputs, attach them to the `Newsletter` model, and surface them via a `format_film_details()` helper used by the HTML template and the Google Calendar plugin.

**Tech Stack:** Flask, Jinja2, jQuery, Google Calendar v3 client, GitPython (unchanged).

**Note on testing:** Per `CLAUDE.md` this project has no automated test suite and no test infrastructure (no pytest, no tests/ directory). Each task uses targeted manual verification (curl, `python -c`, `testtool.py`, browser dev tools) instead of unit tests. Do **not** add a test framework as part of this work.

**Spec:** `docs/superpowers/specs/2026-05-31-movie-year-runtime-design.md`

---

## Task 1: Extend `Newsletter` with year/runtime + `format_film_details`

**Files:**
- Modify: `Newsletter.py`

- [ ] **Step 1: Update constructor signature and attribute init**

In `Newsletter.py`, modify the `__init__` signature to accept `year` and `runtime` as the final two optional kwargs, and store normalized values on `self`.

Replace the existing `__init__` signature and body (lines 29-49) with:

```python
    def __init__(self, city, clubURL, film, filmURL,
                 host, hostURL,
                 location, locationURL,
                 wearing,
                 showTime, synopsis,
                 year=None, runtime=None):
        self.city = city
        self.clubURL = clubURL
        self.film = film.strip()
        self.filmURL = filmURL.strip()
        self.host = host.strip()
        self.hostURL = hostURL.strip()
        self.location = location.strip()
        self.locationURL = locationURL.strip()
        self.wearing = wearing.strip()
        self.showTime = self.normalize_time(showTime)
        self.synopsis = synopsis.strip()
        self.daySuffix = self.get_date_suffix(self.get_next_sunday().day)
        self.year = self._normalize_year(year)
        self.runtime = self._normalize_runtime(runtime)
        # Optional manual override of generated HTML
        self.override_html = None
        # Optional manual override of generated subject
        self.override_subject = None
```

Also remove the now-redundant class-level attribute declarations for `override_html` and `override_subject` if they cause confusion (leave them — they're harmless type hints).

- [ ] **Step 2: Add normalization and formatting helpers**

Add three methods to the `Newsletter` class (place them just after `get_date_suffix`):

```python
    @staticmethod
    def _normalize_year(value):
        if value is None or value == "":
            return None
        try:
            y = int(str(value).strip())
        except (TypeError, ValueError):
            return None
        return y if 1000 <= y <= 9999 else None

    @staticmethod
    def _normalize_runtime(value):
        if value is None or value == "":
            return None
        try:
            r = int(str(value).strip())
        except (TypeError, ValueError):
            return None
        return r if r > 0 else None

    def format_film_details(self) -> str:
        current_year = self.get_next_sunday().year
        parts = []
        if self.year and self.year != current_year:
            parts.append(str(self.year))
        if self.runtime:
            parts.append(f"{self.runtime}m")
        if not parts:
            return ""
        return f" ({', '.join(parts)})"
```

- [ ] **Step 3: Pass `film_details` to the template**

In `generate_HTML()`, add `film_details=self.format_film_details()` to the `template.render(...)` call (currently around line 144). The full call becomes:

```python
        rendered_template = template.render(
            city=self.city,
            clubURL=self.clubURL,
            nextSunday=self.get_next_sunday().strftime("%A, %b %e"),
            daySuffix=self.daySuffix,
            showTime=self.showTime,
            film=self.film,
            filmURL=self.filmURL,
            film_details=self.format_film_details(),
            location=self.location,
            locationURL=self.locationURL,
            host=self.host,
            hostURL=self.hostURL,
            wearing=self.wearing,
            synopsis=synopsis_paragraphs
        )
```

- [ ] **Step 4: Verify `format_film_details` behavior**

From the repo root, run:

```bash
python -c "
from Newsletter import Newsletter
nl = Newsletter('Boston','https://x','Backrooms','https://t','H','','L','','','7pm','syn',
                year=2024, runtime=110)
print(repr(nl.format_film_details()))
nl2 = Newsletter('Boston','https://x','Backrooms','https://t','H','','L','','','7pm','syn',
                 year=2026, runtime=110)
print(repr(nl2.format_film_details()))
nl3 = Newsletter('Boston','https://x','Backrooms','https://t','H','','L','','','7pm','syn',
                 year=2024, runtime=None)
print(repr(nl3.format_film_details()))
nl4 = Newsletter('Boston','https://x','Backrooms','https://t','H','','L','','','7pm','syn')
print(repr(nl4.format_film_details()))
nl5 = Newsletter('Boston','https://x','Backrooms','https://t','H','','L','','','7pm','syn',
                 year='abc', runtime=0)
print(repr(nl5.format_film_details()))
"
```

Expected output (current year is 2026):

```
' (2024, 110m)'
' (110m)'
' (2024)'
''
''
```

If today's actual `get_next_sunday().year` differs from 2026, the first two lines shift accordingly — read for the correct logic, not literal year matching.

- [ ] **Step 5: Commit**

```bash
git add Newsletter.py
git commit -m "Add year/runtime fields and format_film_details helper to Newsletter"
```

---

## Task 2: Render `film_details` in the HTML template

**Files:**
- Modify: `templates/htmlnewsletter.html`

- [ ] **Step 1: Append `{{ film_details }}` after the linked title**

Replace the existing film link line (line 3) with one that appends `film_details` after the `</a>`:

```html
    {% if showTime %} at <b>{{ showTime }}</b>{% endif %} for <a href="{{ filmURL }}">{{ film }}</a>{{ film_details | default('') }} at the
```

The `| default('')` is defensive against older callers that don't pass `film_details`.

- [ ] **Step 2: Verify rendering**

Run:

```bash
python -c "
from Newsletter import Newsletter
nl = Newsletter('Boston','https://snfc','Backrooms','https://tmdb/1','Sean','https://h','Coolidge','https://l','a nametag','7pm','A test synopsis.',
                year=2024, runtime=110)
print(nl.generate_HTML())
"
```

Expected: the output contains `<a href=\"https://tmdb/1\">Backrooms</a> (2024, 110m) at the`.

Also check that omitting `year`/`runtime` still produces sane output (no `(  )` or leftover spaces):

```bash
python -c "
from Newsletter import Newsletter
nl = Newsletter('Boston','https://snfc','Backrooms','https://tmdb/1','Sean','https://h','Coolidge','https://l','a nametag','7pm','syn')
print(nl.generate_HTML())
"
```

Expected: the link line reads `for <a href="https://tmdb/1">Backrooms</a> at the` (no parenthetical).

- [ ] **Step 3: Commit**

```bash
git add templates/htmlnewsletter.html
git commit -m "Append film details suffix after title in newsletter template"
```

---

## Task 3: Plumb `filmYear`/`filmRuntime` through `/api/preview` and POST `/`

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Accept and pass the fields in `/api/preview`**

In `preview_newsletter()` (around line 57), after the existing `data.get(...)` calls, add:

```python
        film_year = data.get('filmYear', '')
        film_runtime = data.get('filmRuntime', '')
```

Then update the `Newsletter(...)` instantiation to pass them as the trailing kwargs:

```python
        nl = Newsletter(
            config.get('clubCity', ''),
            config.get('clubURL', ''),
            film,
            filmURL,
            host_name,
            host_url,
            location_name,
            location_url,
            wearing,
            showTime,
            synopsis,
            year=film_year,
            runtime=film_runtime,
        )
```

- [ ] **Step 2: Accept and pass the fields in `index()` POST**

In `index()` (around line 246), update the `Newsletter(...)` call to include the trailing kwargs:

```python
        nl = Newsletter(config['clubCity'],
                        config['clubURL'],
                        form.get("film", ""),
                        form.get("filmURL", ""),
                        host_name,
                        (config["hosts"][hostIndex]['image'] if (not use_manual and config['hosts']) else ''),
                        location_name,
                        (config["locations"][locationIndex]['link'] if (not use_manual and config['locations']) else ''),
                        form.get("wearing", ""),
                        form.get("showTime", ""),
                        form.get("plotSynopsis", ""),
                        year=form.get("filmYear", ""),
                        runtime=form.get("filmRuntime", ""))
```

- [ ] **Step 3: Verify with curl**

Start the dev server in a separate shell:

```bash
python app.py
```

Then POST a preview with year/runtime included:

```bash
curl -s -X POST http://127.0.0.1:5000/api/preview \
  -H 'Content-Type: application/json' \
  -d '{"film":"Backrooms","filmURL":"https://t","showTime":"7pm","filmYear":"2024","filmRuntime":"110"}' \
  | python -c "import json,sys; d=json.load(sys.stdin); print(d['html'])"
```

Expected: rendered HTML contains `Backrooms</a> (2024, 110m) at the`.

Also verify omitting the fields preserves current behavior:

```bash
curl -s -X POST http://127.0.0.1:5000/api/preview \
  -H 'Content-Type: application/json' \
  -d '{"film":"Backrooms","filmURL":"https://t","showTime":"7pm"}' \
  | python -c "import json,sys; d=json.load(sys.stdin); print(d['html'])"
```

Expected: link line reads `Backrooms</a> at the` (no suffix).

Stop the dev server (`Ctrl-C`).

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "Accept filmYear/filmRuntime in preview and POST handlers"
```

---

## Task 4: Return `Year` and `Runtime` from `/api/movie/details`

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add a helper for safe field extraction**

At module scope in `app.py` (just under the `pluginList = {}` line), add:

```python
def _extract_year(payload):
    raw = payload.get('Year') or payload.get('year')
    if raw:
        s = str(raw).strip()
        if len(s) >= 4 and s[:4].isdigit():
            return s[:4]
    for key in ('release_date', 'releaseDate', 'Released'):
        v = payload.get(key)
        if v and isinstance(v, str) and len(v) >= 4 and v[:4].isdigit():
            return v[:4]
    return ''

def _extract_runtime(payload):
    for key in ('Runtime', 'runtime'):
        v = payload.get(key)
        if v in (None, '', 0):
            continue
        try:
            n = int(str(v).strip().split()[0])
        except (TypeError, ValueError):
            continue
        if n > 0:
            return n
    return 0
```

The `split()[0]` defends against OMDB-style `"110 min"` strings.

- [ ] **Step 2: Use helpers in `/api/movie/details`**

Replace the `return jsonify({...})` block in `movie_details()` (currently lines 204-209) with:

```python
        return jsonify({
            'Title': data.get('Title', ''),
            'tmdbID': data.get('tmdbID', ''),
            'Plot': data.get('Plot', ''),
            'Year': _extract_year(data),
            'Runtime': _extract_runtime(data),
            'Response': 'True' if data.get('Title') else 'False',
        })
```

- [ ] **Step 3: Verify extraction logic without a live moviething service**

Run:

```bash
python -c "
from app import _extract_year, _extract_runtime
print(_extract_year({'Year': '2024'}))
print(_extract_year({'release_date': '2024-09-12'}))
print(_extract_year({'Year': 2024}))
print(_extract_year({}))
print(_extract_runtime({'Runtime': '110 min'}))
print(_extract_runtime({'runtime': 110}))
print(_extract_runtime({'Runtime': 0}))
print(_extract_runtime({}))
"
```

Expected:

```
2024
2024
2024

110
110
0
0
```

- [ ] **Step 4: Verify end-to-end (only if moviething is reachable)**

If you have moviething running locally and configured in `config.json`, start the Flask app and:

```bash
curl -s 'http://127.0.0.1:5000/api/movie/details?id=27205' | python -m json.tool
```

Expected: JSON response contains `Year` (4-digit string) and `Runtime` (positive int) alongside Title/Plot. If moviething is unreachable in your dev environment, skip this step — Step 3 already verified the extraction logic.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "Return Year and Runtime from movie details endpoint"
```

---

## Task 5: Wire hidden inputs and JS for year/runtime

**Files:**
- Modify: `templates/form.html`
- Modify: `static/js/main.js`

- [ ] **Step 1: Add hidden inputs in `form.html`**

Inside the `#filmInfoSet` fieldset, immediately after the `filmURL` input (around line 89, just before the showTime label), add:

```html
                        <input type="hidden" id="filmYear" name="filmYear" value="" />
                        <input type="hidden" id="filmRuntime" name="filmRuntime" value="" />
```

- [ ] **Step 2: Populate hidden fields on movie selection in `main.js`**

In the `.movie-result` click handler (around line 131), inside the `success` callback, set the new fields when the details response contains them. Replace the existing success body with:

```javascript
				success: function (response) {
					if (response.Response === "True") {
						$("#filmSearch").val(response.Title);
						$("#filmURL").val(`https://www.themoviedb.org/movie/${response.tmdbID}`);
						$("#synopsisArea").val(response.Plot);
						$("#filmYear").val(response.Year || '');
						$("#filmRuntime").val(response.Runtime || '');
						$("#searchResults").hide();
						selectedIndex = -1;
					}
				},
```

- [ ] **Step 3: Clear hidden fields when user types into the search box**

The existing `#filmSearch` `input` handler (around line 30) resets `selectedIndex` on every keystroke. Add field-clearing in the same handler. The updated head of the handler:

```javascript
		$("#filmSearch").on('input', function () {
			clearTimeout(searchTimeout);
			const searchTerm = $(this).val();
			selectedIndex = -1;
			$("#filmYear").val('');
			$("#filmRuntime").val('');

			if (searchTerm.length < 2) return;
```

(The dropdown-click handler runs *after* this on a click, and re-fills the values via the details fetch, so user-driven edits clear them and selection re-populates them.)

- [ ] **Step 4: Include the fields in the preview payload**

In `refreshPreview()` (around line 318), add the two fields to the JSON payload:

```javascript
				const payload = {
					hostSelect: $("#hostSelect").val() || '',
					locationSelect: $("#locationSelect").val() || '',
					film: $("#filmSearch").val() || '',
					filmURL: $("#filmURL").val() || '',
					wearing: $("#wearing").val() || '',
					showTime: $("#showTime").val() || '',
					plotSynopsis: $("#synopsisArea").val() || '',
					filmYear: $("#filmYear").val() || '',
					filmRuntime: $("#filmRuntime").val() || '',
					useManualHTML: $useManualHTML.is(":checked"),
					overrideHTML: $overrideHTML.val() || '',
					overrideSubject: $overrideSubject.val() || null
				};
```

- [ ] **Step 5: Manual browser verification**

Start the Flask app (`python app.py`), open `http://127.0.0.1:5000/`, then:

1. Search for a movie, pick one from the dropdown.
2. Open browser dev tools → Elements → inspect `#filmYear` and `#filmRuntime` — both should have non-empty values matching the chosen film.
3. Watch the preview iframe — the linked film title should be followed by ` (YYYY, NNNm)` (or just `(NNNm)` if the film is from the current year).
4. Type a character into the film search box — both hidden inputs should clear, and on next preview refresh the suffix should disappear.
5. Re-select a movie — values repopulate and suffix returns.

- [ ] **Step 6: Commit**

```bash
git add templates/form.html static/js/main.js
git commit -m "Persist film year/runtime via hidden inputs and forward in preview"
```

---

## Task 6: Use runtime to size Google Calendar event

**Files:**
- Modify: `plugins/GoogleCalendarPostingAction.py`

- [ ] **Step 1: Add `timedelta` import and rewrite end-time computation**

At the top of `plugins/GoogleCalendarPostingAction.py`, change the existing `from datetime import datetime` (line 1) to:

```python
from datetime import datetime, timedelta
```

In `execute()`, replace the date/time computation block (currently lines 70-75) with:

```python
            sunday = nl.get_next_sunday()

            (hours, minutes) = self.parse_time(nl.normalize_time(nl.showTime))

            start_dt = sunday.replace(hour=hours, minute=minutes, second=0, microsecond=0)

            runtime_min = getattr(nl, 'runtime', None)
            if runtime_min and runtime_min > 0:
                total_minutes = runtime_min + 60
            else:
                total_minutes = 180  # legacy 3-hour default

            end_dt = start_dt + timedelta(minutes=total_minutes)

            start_time = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000")
            end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000")
```

This also fixes the pre-existing `hour + 3` overflow bug for late showtimes (e.g., 9:30 PM start no longer produces an invalid `24:30:00`).

- [ ] **Step 2: Verify duration math (offline)**

```bash
python -c "
import sys
sys.path.insert(0,'.')
sys.path.insert(0,'plugins')
from GoogleCalendarPostingAction import GoogleCalendarPostingAction
from Newsletter import Newsletter
from datetime import datetime, timedelta

# Mock the time parts of the plugin without invoking Google APIs
nl = Newsletter('Boston','x','Film','https://t','Sean','','Coolidge','','','7:00pm','syn',
                runtime=110)
plug = GoogleCalendarPostingAction()
(h, m) = plug.parse_time(nl.normalize_time(nl.showTime))
start = nl.get_next_sunday().replace(hour=h, minute=m, second=0, microsecond=0)
total = nl.runtime + 60 if nl.runtime else 180
end = start + timedelta(minutes=total)
print(f'start={start.isoformat()} end={end.isoformat()} duration_min={(end-start).total_seconds()/60:.0f}')
"
```

Expected: `duration_min=170` (110 + 60).

Re-run with `runtime=None` instead of `runtime=110`:

```bash
python -c "
import sys
sys.path.insert(0,'.')
sys.path.insert(0,'plugins')
from GoogleCalendarPostingAction import GoogleCalendarPostingAction
from Newsletter import Newsletter
from datetime import timedelta
nl = Newsletter('Boston','x','Film','https://t','Sean','','Coolidge','','','9:30pm','syn')
plug = GoogleCalendarPostingAction()
(h, m) = plug.parse_time(nl.normalize_time(nl.showTime))
start = nl.get_next_sunday().replace(hour=h, minute=m, second=0, microsecond=0)
total = nl.runtime + 60 if nl.runtime else 180
end = start + timedelta(minutes=total)
print(f'start={start.isoformat()} end={end.isoformat()} duration_min={(end-start).total_seconds()/60:.0f}')
"
```

Expected: `duration_min=180`, and the `end` time correctly rolls past midnight (e.g., `00:30:00` on the following day).

- [ ] **Step 3: Commit**

```bash
git add plugins/GoogleCalendarPostingAction.py
git commit -m "Size Google Calendar events from movie runtime + 60m dinner pad"
```

---

## Task 7: Add `--year` and `--runtime` flags to `testtool.py`

**Files:**
- Modify: `testtool.py`

- [ ] **Step 1: Add CLI flags and pass to Newsletter**

In `main()` (around line 113, just below `--synopsis`), add:

```python
    parser.add_argument("--year", type=int, default=None, help="Film release year")
    parser.add_argument("--runtime", type=int, default=None, help="Film runtime in minutes")
```

Then update the `Newsletter(...)` call (around line 132) to pass them:

```python
    nl = Newsletter(
        config.get("clubCity", ""),
        config.get("clubURL", ""),
        args.film,
        args.film_url,
        host_name,
        host_url,
        location_name,
        location_url,
        args.wearing,
        args.show_time,
        args.synopsis,
        year=args.year,
        runtime=args.runtime,
    )
```

- [ ] **Step 2: Verify CLI**

Run a plugin that doesn't touch external services. The Hugo plugin writes to a local repo — if you don't want side effects, just dry-run with an invalid plugin name to confirm Newsletter accepts the kwargs without error:

```bash
python testtool.py --plugin "NonexistentPlugin" --film "Backrooms" --year 2024 --runtime 110 --time 7:00pm
```

Expected: prints `[SKIP] Plugin not found: NonexistentPlugin` and exits with code 2. Crucially, no `TypeError` from the `Newsletter(...)` call.

For a true end-to-end test (only if `config.json` has the Mailing List plugin disabled or you're OK with side effects), pick any plugin you're comfortable invoking.

- [ ] **Step 3: Commit**

```bash
git add testtool.py
git commit -m "Add --year and --runtime flags to testtool CLI"
```

---

## Task 8: End-to-end manual verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full browser flow**

Start the dev server (`python app.py`) and open the form in a browser. Run through this checklist, watching the live preview iframe:

| Case | Expected |
| --- | --- |
| Search and select a film released before the current year | Title in preview reads `Film (YYYY, NNNm)` |
| Search and select a film released in the current year | Title reads `Film (NNNm)` |
| Type a film title manually (no search) | Title reads `Film` with no parenthetical |
| Select a film, then edit the title text | Suffix disappears after edit |
| Re-select same film via search | Suffix reappears |

- [ ] **Step 2: Visual check the rendered HTML body**

In the preview iframe, the link should be `<a href="...">Film</a> (YYYY, NNNm)` — the parenthetical lives outside the link (not clickable), per spec.

- [ ] **Step 3: (Optional) Verify Google Calendar event**

If you have a calendar account configured and don't mind a test event:

```bash
python testtool.py --plugin "Google Calendar" --film "Test - Please Ignore" \
  --film-url https://example.com --time 7:00pm --year 2024 --runtime 110
```

Then open the event in Google Calendar and confirm duration is 2h 50m (110+60).

- [ ] **Step 4: Final commit (if any cleanup was needed)**

If steps 1-3 surface any small issues you needed to patch, commit them. Otherwise this task has no commit.

---

## Done

The user-visible deliverables:
1. Newsletter preview shows year/runtime in the film title line.
2. Google Calendar events for plugin-posted screenings end at `start + runtime + 60m`.
3. Manual film entries continue to work with the previous 3-hour calendar default.
