import requests

from BasePostingAction import BasePostingAction


class ListmonkPostingAction(BasePostingAction):
    pluginName = "Listmonk"
    configSection = "listmonk"

    def execute(self, config, nl):
        self.config = config

        url = self.read_config_value('url').rstrip('/')
        username = self.read_config_value('username')
        password = self.read_config_value('password')
        list_ids = self.read_config_value('listIds')

        if not url:
            raise ValueError("Listmonk url not configured")
        if not username or not password:
            raise ValueError("Listmonk username/password not configured")
        if not list_ids:
            raise ValueError("Listmonk listIds not configured")

        auth = (username, password)
        subject = nl.generate_subject()
        body = nl.generate_HTML()

        # Create the campaign
        campaign_payload = {
            "name": subject,
            "subject": subject,
            "body": body,
            "content_type": "html",
            "type": "regular",
            "lists": list_ids,
        }

        resp = requests.post(
            f"{url}/api/campaigns",
            json=campaign_payload,
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        campaign = resp.json().get("data", {})
        campaign_id = campaign.get("id")

        if not campaign_id:
            raise RuntimeError("Listmonk did not return a campaign ID")

        # Start the campaign immediately
        resp = requests.put(
            f"{url}/api/campaigns/{campaign_id}/status",
            json={"status": "running"},
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()

        campaign_url = f"{url}/campaigns/{campaign_id}"
        return f"Posted to <a href='{campaign_url}'>Listmonk</a><br />"
