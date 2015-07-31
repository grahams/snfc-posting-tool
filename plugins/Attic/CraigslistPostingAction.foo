from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

import cgi

class CraigslistPostingAction(BasePostingAction):
    pluginName = "Craigslist Text Generator (must manually post)"
    configSection = 'craigslist'

    def execute(self, config, nl):
        self.config = config

        clURL = self.readConfigValue('url')

        print "<br />"
        print "Copy/Paste this into your <a href='" + clURL + "'>Craigslist Posting</a>:<br />"
        print "<br />"
        print cgi.escape(str(nl.generateCraigslist()))
        print "<br />"
        print "<br />"
