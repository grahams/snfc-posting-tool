# Moviething Search Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace OMDB movie search with proxied calls to the moviething TMDB-based API, including advanced filtering UI.

**Architecture:** The Flask backend proxies search/detail requests to moviething over a shared Docker network, forwarding the Authentik `x-authentik-username` header. The frontend JS calls the Flask proxy endpoints and renders results in the existing dropdown pattern. A collapsible `<details>` element provides TMDB filter controls.

**Tech Stack:** Python/Flask (backend proxy), jQuery (frontend), TMDB via moviething's Express API

**Design doc:** `docs/plans/2026-03-06-moviething-search-integration-design.md`

---

### Task 1: Update config.example.json

**Files:**
- Modify: `config.example.json`

**Step 1: Read current config.example.json and update it**

Remove the `omdb` section. Add `moviething` section:

```json
"moviething": {
    "baseUrl": "http://moviething:3000/api"
}
```

The full file should look like:

```json
{
  "clubCity": "Boston",
  "clubURL": "https://boston.sundaynightfilmclub.com/",
  "hosts": [
    {
      "name": "Sean",
      "image": "https://example.com/hosts/sean.jpg"
    },
    {
      "name": "Alex",
      "image": "https://example.com/hosts/alex.jpg"
    }
  ],
  "locations": [
    {
      "name": "Example Cinema",
      "link": "https://example.com/cinemas/example"
    }
  ],
  "moviething": {
      "baseUrl": "http://moviething:3000/api"
  },
  "mailingList": {
    "enabled": true,
    "sender": "host@example.com",
    "recipient": "announce@example.com",
    "url": "https://lists.example.com/listinfo/snfc",
    "smtpUsername": "",
    "smtpPassword": "",
    "smtpHostname": "localhost",
    "smtpPort": 1025,
    "smtpUseSSL": false,
    "smtpUseStartTLS": false
  },
  "hugo": {
    "enabled": false,
    "gitRepoDir": "/path/to/your/hugo/site",
    "contentDir": "content/posts",
    "sshKeyPath": ""
  },
  "googleCalendar": {
    "enabled": false,
    "calendarId": "your_calendar_id@group.calendar.google.com"
  },
  "mastodon": {
    "enabled": false,
    "instanceUrl": "https://mastodon.social",
    "accessToken": "YOUR_MASTODON_ACCESS_TOKEN",
    "visibility": "public",
    "language": "en"
  },
  "bluesky": {
    "enabled": false,
    "service": "https://bsky.social",
    "handle": "you.example.bsky.social",
    "appPassword": "YOUR_BSKY_APP_PASSWORD"
  }
}
```

**Step 2: Commit**

```bash
git add config.example.json
git commit -m "Replace OMDB config with moviething baseUrl in example config"
```

---

### Task 2: Replace OMDB proxy endpoints with moviething proxy endpoints in app.py

**Files:**
- Modify: `app.py` (lines 114-132: the two OMDB endpoints)

**Step 1: Replace the OMDB endpoints**

Remove the `/api/omdb/search` endpoint (lines 114-122) and `/api/omdb/movie` endpoint (lines 124-132). Replace with two new endpoints:

```python
@app.route('/api/movie/search')
def movie_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    base_url = config.get('moviething', {}).get('baseUrl', '')
    if not base_url:
        return jsonify({'error': 'moviething not configured'}), 500

    # Build filter payload from query params
    payload = {'title': query}
    for param, key in [
        ('exclude_videos', 'exclude_videos'),
        ('min_popularity', 'min_popularity'),
        ('max_popularity', 'max_popularity'),
        ('min_vote_count', 'min_vote_count'),
        ('max_vote_count', 'max_vote_count'),
        ('min_vote_average', 'min_vote_average'),
        ('max_vote_average', 'max_vote_average'),
        ('min_release_date', 'min_release_date'),
        ('max_release_date', 'max_release_date'),
    ]:
        val = request.args.get(param)
        if val is not None and val != '':
            if param == 'exclude_videos':
                payload[key] = val.lower() in ('true', '1', 'yes')
            elif 'date' in param:
                payload[key] = val
            else:
                try:
                    payload[key] = float(val)
                except ValueError:
                    pass

    # Forward Authentik header
    headers = {}
    authentik_user = request.headers.get('x-authentik-username')
    if authentik_user:
        headers['x-authentik-username'] = authentik_user

    try:
        resp = requests.post(
            f'{base_url}/searchMovie',
            data={'json': json.dumps(payload)},
            headers=headers,
            timeout=10,
        )
        data = resp.json()
        # Translate to our expected shape
        results = []
        for movie in data.get('Search', []):
            results.append({
                'Title': movie.get('Title', ''),
                'Year': movie.get('Year', ''),
                'tmdbID': movie.get('tmdbID', ''),
                'Poster': movie.get('Poster', ''),
            })
        return jsonify({'Search': results, 'Response': 'True' if results else 'False'})
    except requests.RequestException:
        return jsonify({'Search': [], 'error': 'Movie search unavailable'})


@app.route('/api/movie/details')
def movie_details():
    tmdb_id = request.args.get('id', '')
    if not tmdb_id:
        return jsonify({'error': 'TMDB ID is required'}), 400

    base_url = config.get('moviething', {}).get('baseUrl', '')
    if not base_url:
        return jsonify({'error': 'moviething not configured'}), 500

    headers = {}
    authentik_user = request.headers.get('x-authentik-username')
    if authentik_user:
        headers['x-authentik-username'] = authentik_user

    try:
        resp = requests.post(
            f'{base_url}/getMovieDetails',
            data={'json': json.dumps({'tmdbID': int(tmdb_id)})},
            headers=headers,
            timeout=10,
        )
        data = resp.json()
        return jsonify({
            'Title': data.get('Title', ''),
            'imdbID': data.get('imdbID', ''),
            'Plot': data.get('Plot', ''),
            'Response': 'True' if data.get('Title') else 'False',
        })
    except requests.RequestException:
        return jsonify({'error': 'Movie details unavailable'})
```

**Step 2: Verify no remaining references to `omdb` in app.py**

Search for `omdb` in the file — there should be none.

**Step 3: Commit**

```bash
git add app.py
git commit -m "Replace OMDB endpoints with moviething proxy endpoints"
```

---

### Task 3: Update frontend JS to use new endpoints and add filter UI

**Files:**
- Modify: `static/js/main.js` (lines 26-119: search and selection logic)

**Step 1: Replace the search AJAX call (lines 30-59)**

Replace the search handler to call `/api/movie/search` with filter params:

```javascript
$("#filmSearch").on('input', function () {
    clearTimeout(searchTimeout);
    const searchTerm = $(this).val();
    selectedIndex = -1;

    if (searchTerm.length < 2) return;

    searchTimeout = setTimeout(() => {
        // Gather filter values
        const params = new URLSearchParams({ q: searchTerm });
        const filterMap = {
            'excludeVideos': 'exclude_videos',
            'minPopularity': 'min_popularity',
            'maxPopularity': 'max_popularity',
            'minVoteCount': 'min_vote_count',
            'maxVoteCount': 'max_vote_count',
            'minVoteAverage': 'min_vote_average',
            'maxVoteAverage': 'max_vote_average',
            'minReleaseDate': 'min_release_date',
            'maxReleaseDate': 'max_release_date',
        };
        for (const [elemId, paramName] of Object.entries(filterMap)) {
            const $el = $(`#${elemId}`);
            if ($el.length) {
                if ($el.is(':checkbox')) {
                    if ($el.is(':checked')) params.set(paramName, 'true');
                } else if ($el.val()) {
                    params.set(paramName, $el.val());
                }
            }
        }

        $.ajax({
            url: `api/movie/search?${params.toString()}`,
            method: 'GET',
            success: function (response) {
                if (response.Response === "True") {
                    const results = response.Search
                        .sort((a, b) => parseInt(b.Year) - parseInt(a.Year));
                    const resultsHtml = results.map(movie => `
                        <div class="movie-result" data-tmdbid="${movie.tmdbID}" tabindex="-1">
                            ${movie.Title} (${movie.Year})
                        </div>
                    `).join('');

                    $("#searchResults")
                        .html(resultsHtml)
                        .show();
                } else {
                    $("#searchResults").hide();
                }
            }
        });
    }, 300);
});
```

**Step 2: Replace movie selection handler (lines 103-119)**

Update click handler to use tmdbID and the new details endpoint:

```javascript
$(document).on('click', '.movie-result', function () {
    const tmdbID = $(this).data('tmdbid');

    $.ajax({
        url: `api/movie/details?id=${tmdbID}`,
        method: 'GET',
        success: function (response) {
            if (response.Response === "True") {
                $("#filmSearch").val(response.Title);
                $("#filmURL").val(`https://www.imdb.com/title/${response.imdbID}/`);
                $("#synopsisArea").val(response.Plot);
                $("#searchResults").hide();
                selectedIndex = -1;
            }
        }
    });
});
```

**Step 3: Add filter change triggers**

After the filter UI exists (Task 4), filter changes should re-trigger search. Add at the end of `$(document).ready`:

```javascript
// Re-trigger search when filters change
$(document).on('change input', '#excludeVideos, #minPopularity, #maxPopularity, #minVoteCount, #maxVoteCount, #minVoteAverage, #maxVoteAverage, #minReleaseDate, #maxReleaseDate', function () {
    const searchTerm = $("#filmSearch").val();
    if (searchTerm && searchTerm.length >= 2) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            $("#filmSearch").trigger('input');
        }, 300);
    }
});
```

**Step 4: Commit**

```bash
git add static/js/main.js
git commit -m "Update frontend to use moviething search API with filter support"
```

---

### Task 4: Add filter UI to form.html

**Files:**
- Modify: `templates/form.html` (inside `#filmInfoSet` fieldset, after the `#searchResults` div on line 52)

**Step 1: Add collapsible filter panel**

Insert after line 52 (`<div id="searchResults" style="display: none;"></div>`):

```html
<details id="searchFilters">
    <summary>Search Filters</summary>
    <div class="filter-grid">
        <label class="checkbox-label">
            <input type="checkbox" id="excludeVideos" />
            Exclude videos
        </label>
        <div class="filter-row">
            <label for="minPopularity">Popularity:</label>
            <input type="number" id="minPopularity" placeholder="Min" step="any" />
            <span>to</span>
            <input type="number" id="maxPopularity" placeholder="Max" step="any" />
        </div>
        <div class="filter-row">
            <label for="minVoteCount">Vote count:</label>
            <input type="number" id="minVoteCount" placeholder="Min" />
            <span>to</span>
            <input type="number" id="maxVoteCount" placeholder="Max" />
        </div>
        <div class="filter-row">
            <label for="minVoteAverage">Rating:</label>
            <input type="number" id="minVoteAverage" placeholder="Min" step="0.1" min="0" max="10" />
            <span>to</span>
            <input type="number" id="maxVoteAverage" placeholder="Max" step="0.1" min="0" max="10" />
        </div>
        <div class="filter-row">
            <label for="minReleaseDate">Release date:</label>
            <input type="date" id="minReleaseDate" />
            <span>to</span>
            <input type="date" id="maxReleaseDate" />
        </div>
    </div>
</details>
```

**Step 2: Commit**

```bash
git add templates/form.html
git commit -m "Add collapsible search filter panel to form"
```

---

### Task 5: Add CSS for the filter panel

**Files:**
- Modify: `static/tool.css` (append at end)

**Step 1: Add filter styles**

Append to the end of `static/tool.css`:

```css
/* Search filter panel */
#searchFilters {
    margin: 8px 0 12px;
}

#searchFilters summary {
    cursor: pointer;
    font-size: 13px;
    color: #555;
    user-select: none;
}

#searchFilters summary:hover {
    color: #333;
}

.filter-grid {
    padding: 10px 0 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.filter-row {
    display: grid;
    grid-template-columns: 90px 1fr auto 1fr;
    gap: 6px;
    align-items: center;
}

.filter-row label {
    font-size: 13px;
    margin: 0 !important;
}

.filter-row span {
    font-size: 12px;
    color: #888;
    text-align: center;
}

.filter-row input {
    font-size: 13px;
    padding: 4px 6px;
    margin: 0 !important;
}

#searchFilters .checkbox-label {
    font-size: 13px;
    padding: 2px 0;
}
```

**Step 2: Commit**

```bash
git add static/tool.css
git commit -m "Add CSS for search filter panel"
```

---

### Task 6: Update example-compose.yml for shared Docker network

**Files:**
- Modify: `example-compose.yml`

**Step 1: Add shared network to both services**

Add a `moviething` external network to each service's `networks` list. The services already use a `proxy` external network. Add:

```yaml
networks:
    proxy:
        external: true
    moviething:
        external: true
```

And add `moviething` to each service's networks. For example, `boston-posting-tool`:

```yaml
        networks:
            - proxy
            - moviething
```

**Step 2: Commit**

```bash
git add example-compose.yml
git commit -m "Add shared moviething network to example compose config"
```

---

### Task 7: Manual integration test

**Step 1: Verify the full flow works**

1. Ensure moviething is running and both containers share a Docker network
2. Update your local `config.json` to replace `omdb` with `moviething.baseUrl`
3. Start snfc-posting-tool: `python app.py`
4. Open the form in browser
5. Type a movie title (>= 2 chars) in the Film Title field
6. Verify search results appear in the dropdown
7. Click a result — verify Title, Film URL (IMDB link), and Plot Synopsis populate
8. Open the "Search Filters" disclosure triangle
9. Set a filter (e.g., min vote count = 100), re-type a search
10. Verify filtered results are returned

**Step 2: Final commit**

```bash
git add -A
git commit -m "Complete moviething search integration: remove OMDB, add TMDB proxy with filters"
```
