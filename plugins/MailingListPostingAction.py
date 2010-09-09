from Newsletter import Newsletter
from BasePostingAction import BasePostingAction

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class MailingListPostingAction(BasePostingAction):
    pluginName = "SNFC Mailing List"
    configSection = 'mailingList'
    
    def execute(self, config, nl):
        self.config = config 

        sender = self.readConfigValue('sender')
        recipient = self.readConfigValue('recipient')
        url = self.readConfigValue('url')
    
        msg = MIMEMultipart("alternative")
        msg['Subject'] = nl.generateSubject()
        msg['From'] = sender
        msg['To'] = recipient
        msg.preamble = nl.generatePlainText()
        msg.epilogue = ''
    
        plain = MIMEText(str( nl.generatePlainText() ), "plain")
        html = MIMEText(str( nl.generateHTML() ), "html")
    
        msg.attach(plain)
        msg.attach(html)
    
        s = smtplib.SMTP()
        s.connect()
        s.sendmail(sender, recipient, msg.as_string())
        s.close()

        print "Posted to the <a href='" + url + "'>Mailing List</a><br />"
