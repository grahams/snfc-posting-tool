from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

import wordpresslib

class WordPressPostingAction(BasePostingAction):
    pluginName = "SNFC Site"
    configSection = 'wordpress'
    config = None

    def execute(self, config, nl):
        self.config = config

        username = self.readConfigValue('username')
        password = self.readConfigValue('password')
        xmlrpc = self.readConfigValue('xmlrpc')
        blogId = self.readConfigValue('blogId')
        url = self.readConfigValue('url')

        wp = wordpresslib.WordPressClient(xmlrpc, username, password)
        wp.selectBlog(0)

        post = wordpresslib.WordPressPost()

        post.title = nl.generateSubject()
        post.description = str(nl.generateHTML())
        post.categories = (wp.getCategoryIdFromName('Newsletters'),)

        idPost = wp.newPost(post, True)

        pURL = url + "?p=" + str(idPost)

        print 'Posted to the <a href="%s">SNFC Webpage</a>.<br />' % pURL 
