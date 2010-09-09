from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

import cgi

class CraigslistPostingAction(BasePostingAction):
    pluginName = "Craigslist Text Generator (you still have to post it yourself)"

    def execute(self, config, nl):
        print "<br />"
        print "Copy/Paste this into your <a href='https://post.craigslist.org/bos/E/eve/gbs'>Craigslist Posting</a>:<br />"
        print "<br />"
        print cgi.escape(str(nl.generateCraigslist()))
        print "<br />"
        print "<br />"
