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

        username = self.readConfigValue('username')
        password = self.readConfigValue('password')
        jsonApiUrl = self.readConfigValue('jsonApiUrl')
        blogId = self.readConfigValue('blogId')
        url = self.readConfigValue('url')

        wpCredentials = f"{username}:{password}"
        wpToken = base64.b64encode(wpCredentials.encode())
        wpHeader = {'Authorization': 'Basic ' + wpToken.decode('utf-8')}

        data = {
            "title":f"{nl.generateSubject()}",
            "content":f"{nl.generateHTML()}",
            "status": "publish"
        }

        response = requests.post(jsonApiUrl,headers=wpHeader, json=data)
        response = json.loads(response.text);

        postUrl = response['link']
        
        return(f'Posted to the <a href="{postUrl}">SNFC Webpage</a>.<br />')
