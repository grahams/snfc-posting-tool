import requests
import json
import base64

from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

class WordPressPostingAction(BasePostingAction):
    pluginName = "SNFC Site"
    configSection = 'wordpress'
    config = None

    def execute(self, config, nl):
        self.config = config

        username = self.read_config_value('username')
        password = self.read_config_value('password')
        jsonApiUrl = self.read_config_value('jsonApiUrl')
        blogId = self.read_config_value('blogId')
        url = self.read_config_value('url')

        wpCredentials = f"{username}:{password}"
        wpToken = base64.b64encode(wpCredentials.encode())
        wpHeader = {'Authorization': 'Basic ' + wpToken.decode('utf-8')}

        data = {
            "title":f"{nl.generateSubject()}",
            "content":f"{nl.generateHTML()}",
            "status": "publish"
        }

        response = requests.post(jsonApiUrl,headers=wpHeader, json=data) # type: ignore
        response = json.loads(response.text)

        postUrl = response['link']
        
        return(f'Posted to the <a href="{postUrl}">SNFC Webpage</a>.<br />')
