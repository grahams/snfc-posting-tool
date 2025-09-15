import requests
import datetime
import re

from BasePostingAction import BasePostingAction


class BlueskyPostingAction(BasePostingAction):
    pluginName = "Bluesky"
    configSection = "bluesky"
    config = None

    def _build_status(self, nl) -> str:
        # Use the generic short-form generator
        base_text = nl.generate_short_text() if hasattr(nl, 'generate_short_text') else nl.generate_twitter()
        link = (nl.filmURL or nl.clubURL or '').strip()

        # If manual HTML was used to derive text, don't append link here; rely on text
        if nl.override_html:
            status = base_text
        else:
            if link:
                # Ensure scheme so it's recognized as a URL
                if not re.match(r'^https?://', link, flags=re.IGNORECASE):
                    link = f"https://{link}"

                limit = 300
                space_and_link_len = 1 + len(link)
                if len(base_text) + space_and_link_len <= limit:
                    status = f"{base_text} {link}"
                else:
                    # Trim base text but keep the full link intact
                    available_for_text = max(0, limit - space_and_link_len)
                    if available_for_text >= 3:
                        trimmed = base_text[: available_for_text - 3] + "..."
                    else:
                        trimmed = base_text[: available_for_text]
                    status = f"{trimmed} {link}".strip()
            else:
                status = base_text

        # Final hard cap at 300 for safety
        if len(status) > 300:
            status = status[:297] + "..."
        return status

    def _build_facets(self, text: str):
        """Create Bluesky richtext facets for URLs in the text so they are clickable."""
        facets = []
        for match in re.finditer(r'https?://[^\s)\]\"<>]+', text):
            url = match.group(0)
            # Compute UTF-8 byte offsets as required by Bluesky richtext
            byte_start = len(text[: match.start()].encode('utf-8'))
            byte_end = len(text[: match.end()].encode('utf-8'))
            facets.append({
                "index": {"byteStart": byte_start, "byteEnd": byte_end},
                "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
            })
        return facets

    def execute(self, config, nl):
        self.config = config

        # Read config safely without raising KeyError for optional fields
        section = (config or {}).get(self.configSection, {})
        service = section.get('service') or 'https://bsky.social'
        handle = section.get('handle')
        password = section.get('appPassword') or section.get('password')

        if not handle:
            raise ValueError("Bluesky handle not configured")
        if not password:
            raise ValueError("Bluesky appPassword/password not configured")

        api_base = service.rstrip('/')

        # 1) Create session
        session_payload = {
            "identifier": handle,
            "password": password,
        }
        resp = requests.post(f"{api_base}/xrpc/com.atproto.server.createSession", json=session_payload, timeout=20)
        resp.raise_for_status()
        session = resp.json()
        access_jwt = session.get('accessJwt') or session.get('accessToken')
        did = session.get('did')
        if not access_jwt or not did:
            raise RuntimeError("Failed to authenticate with Bluesky: missing token or DID")

        # 2) Post a status with richtext facets for URLs so links are clickable
        text = self._build_status(nl)
        facets = self._build_facets(text)
        headers = { 'Authorization': f"Bearer {access_jwt}" }
        post_payload = {
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": {
                "$type": "app.bsky.feed.post",
                "text": text,
                **({"facets": facets} if facets else {}),
                "createdAt": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
            }
        }

        resp = requests.post(f"{api_base}/xrpc/com.atproto.repo.createRecord", json=post_payload, headers=headers, timeout=20)
        resp.raise_for_status()
        payload = resp.json()

        # Construct a web URL for the post
        # Most servers host at https://bsky.app/profile/{did or handle}/post/{rkey}
        rkey = ((payload.get('uri') or '').split('/')[-1]) if payload.get('uri') else ''
        profile = handle
        web_base = 'https://bsky.app'
        url = f"{web_base}/profile/{profile}/post/{rkey}" if rkey else web_base

        return (f"Posted to <a href='{url}'>Bluesky</a><br />")


