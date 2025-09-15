import requests

from BasePostingAction import BasePostingAction


class MastodonPostingAction(BasePostingAction):
    pluginName = "Mastodon"
    configSection = "mastodon"
    config = None

    def _build_status(self, nl) -> str:
        base_text = nl.generate_twitter()
        link = nl.filmURL or nl.clubURL
        if link:
            status = f"{base_text} {link}"
        else:
            status = base_text

        # Mastodon default max length is 500 characters
        if len(status) > 500:
            status = status[:497] + "..."
        return status

    def execute(self, config, nl):
        self.config = config

        instance_url = self.read_config_value('instanceUrl')
        access_token = self.read_config_value('accessToken')
        visibility = self.read_config_value('visibility') if self.read_config_value('visibility') else 'public'
        language = self.read_config_value('language') if self.read_config_value('language') else 'en'

        if not instance_url:
            raise ValueError("Mastodon instanceUrl not configured")
        if not access_token:
            raise ValueError("Mastodon accessToken not configured")

        api_base = instance_url.rstrip('/')

        status_text = self._build_status(nl)

        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        data = {
            'status': status_text,
            'visibility': visibility,
            'language': language,
        }

        resp = requests.post(f"{api_base}/api/v1/statuses", headers=headers, data=data, timeout=15)
        resp.raise_for_status()
        payload = resp.json()

        url = payload.get('url')
        if not url:
            # Fallback construction if url missing
            acct = (payload.get('account') or {}).get('acct', '')
            sid = payload.get('id', '')
            url = f"{api_base}/@{acct}/{sid}" if acct and sid else api_base

        return (f"Posted to <a href='{url}'>Mastodon</a><br />")


