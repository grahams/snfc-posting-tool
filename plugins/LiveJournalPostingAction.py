from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

import warnings

from lj import lj

class LiveJournalPostingAction(BasePostingAction):
    pluginName = "LiveJournal Community"
    config = None
    configSection = 'liveJournal'
    
    def execute(self, config, nl):
        self.config = config

        username = self.readConfigValue('username')
        password = self.readConfigValue('password')
        communityName = self.readConfigValue('communityName')
        url = self.readConfigValue('url')

        subject = unicode("[snfc] " + nl.generateSubject())
        content = unicode( nl.generateHTML() )

        props = {'opt_preformatted': True}

        ljclient = lj.LJServer("SNFC-LJ-Tool/1.0",
                "https://github.com/grahams/snfc-posting-tool; info@sundaynightfilmclub.com")
        ljclient.login(username, password)
        ljclient.postevent(content, subject=subject, usejournal=unicode(communityName), props=props)

        print "Posted to the <a href='http://community.livejournal.com/" + communityName + "/'>" + communityName + " LiveJournal</a> <br />"
