from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

import cgi

from twitter import *

class TwitterPostingAction(BasePostingAction):
    pluginName = "Twitter"
    configSection = 'twitter'
    config = None

    def execute(self, config, nl):
        self.config = config

        accountName = self.readConfigValue('accountName')
        OAuthConsumerKey = self.readConfigValue('OAuthConsumerKey')
        OAuthConsumerSecret = self.readConfigValue('OAuthConsumerSecret')
        OAuthUserToken = self.readConfigValue('OAuthUserToken')
        OAuthUserTokenSecret = self.readConfigValue('OAuthUserTokenSecret')

        t = Twitter( auth=OAuth(OAuthUserToken, OAuthUserTokenSecret, OAuthConsumerKey, OAuthConsumerSecret) )

        t.statuses.update(status=nl.generateTwitter())

        print "Posted to the <a href='http://twitter.com/" + accountName + "'>SNFC Twitter Account</a><br />"
