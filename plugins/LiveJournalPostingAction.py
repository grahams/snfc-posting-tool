from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

import warnings
import livejournal

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

        lj = livejournal.LiveJournal("SNFC-LJ-Tool/1.0")
        lj.login(username, password)
        lj.postevent(content, subject=subject, usejournal=unicode(communityName), props=props)

        print "Posted to the <a href='http://community.livejournal.com/" + communityName + "/'>" + communityName + " LiveJournal</a> <br />"
