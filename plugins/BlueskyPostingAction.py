import requests
import datetime

from BasePostingAction import BasePostingAction


class BlueskyPostingAction(BasePostingAction):
    pluginName = "Bluesky"
    configSection = "bluesky"
    config = None

    def _build_status(self, nl) -> str:
        base_text = nl.generate_twitter()
        link = nl.filmURL or nl.clubURL
        status = f"{base_text} {link}".strip()

        # Bluesky recommended limit ~300 chars for readability; hard wrap at 300
        if len(status) > 300:
            status = status[:297] + "..."
        return status

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

        # 2) Post a status (rich text not required for a simple link+text post)
        text = self._build_status(nl)
        headers = { 'Authorization': f"Bearer {access_jwt}" }
        post_payload = {
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": {
                "$type": "app.bsky.feed.post",
                "text": text,
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


